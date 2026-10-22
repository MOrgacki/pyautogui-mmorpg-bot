import time

import cv2
import numpy as np

from detection.Components import ComponentType, DetectedComponent, GAME_VIEW_TILES, Layout, Region
from detection.Templates import Templates


def check_image(image):
    if image is None or not hasattr(image, 'ndim') or image.ndim != 3 or image.shape[2] != 3 or image.size == 0:
        raise ValueError('expected a non-empty BGR image')


def match_template(image, template):
    """ Best TM_CCOEFF_NORMED match: (score, (x, y)), or (0.0, None) if the template does not fit.
    Ties go to the top-most, then left-most position (minMaxLoc scans row by row). """
    if template.shape[0] > image.shape[0] or template.shape[1] > image.shape[1]:
        return 0.0, None
    result = cv2.matchTemplate(image, template, cv2.TM_CCOEFF_NORMED)
    # Flat image areas give NaN or inf scores
    result = np.nan_to_num(result, nan=0.0, posinf=0.0, neginf=0.0)
    _, score, _, location = cv2.minMaxLoc(result)
    return float(score), location


def derive_region(anchor, geometry, scale, image_size):
    """ Component region from its anchor box and anchor-relative geometry, clipped to the image """
    dx, dy, width, height = geometry
    width = anchor.width if width < 0 else round(width * scale)
    height = anchor.height if height < 0 else round(height * scale)
    x = anchor.x + round(dx * scale)
    y = anchor.y + round(dy * scale)
    image_width, image_height = image_size
    x0, y0 = max(0, x), max(0, y)
    x1, y1 = min(image_width, x + width), min(image_height, y + height)
    if x1 <= x0 or y1 <= y0:
        return None
    return Region(x0, y0, x1 - x0, y1 - y0)


# A scale whose anchor matches at least this well is taken without trying the others
CLEAR_MATCH = 0.97


def find_scale(gray, templates, config):
    """ Scale at which the scale anchor matches best """
    name = config.anchor_templates[config.scale_anchor][0]
    best_scale, best_score = 1.0, -1.0
    for scale in config.scales:
        score, _ = match_template(gray, templates.get(name, scale, gray=True))
        if score > best_score:
            best_scale, best_score = scale, score
        if score >= CLEAR_MATCH:
            break
    return best_scale if best_score >= config.match_threshold else 1.0


def find_anchor(gray, templates, names, scale):
    """ Best match among template variants on a grayscale image: (score, location, name, template) """
    best = (0.0, None, names[0], None)
    for name in names:
        template = templates.get(name, scale, gray=True)
        score, location = match_template(gray, template)
        if location is not None and score > best[0]:
            best = (score, location, name, template)
    return best


def find_game_view(image, config):
    """ Largest axis-aligned rectangle with the 15:11 tile aspect ratio (research R6) """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 30, 90)
    # Close small gaps in the frame's edge without growing it
    edges = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))
    contours, _ = cv2.findContours(edges, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    best = None
    for contour in contours:
        x, y, width, height = cv2.boundingRect(contour)
        if width < config.game_view_min_width or height == 0:
            continue
        aspect = width / height
        if abs(aspect - config.game_view_aspect) / config.game_view_aspect > config.aspect_tolerance:
            continue
        if best is None or width * height > best.width * best.height:
            best = Region(x, y, width, height)
    if best is None:
        return DetectedComponent.missing(ComponentType.GAME_VIEW, 'game view not found')
    return DetectedComponent(ComponentType.GAME_VIEW, True, best, 1.0, 1.0,
                             {'tile_size': best.width / GAME_VIEW_TILES[0]})


def detect_layout(image, templates, config, window_hwnd=0, generation=0):
    """ Finds every component in a capture of the client area. See contracts/layout-detector.md """
    check_image(image)
    image_height, image_width = image.shape[:2]
    min_width, min_height = templates.smallest_size()
    if image_width < min_width or image_height < min_height:
        return Layout.empty(window_hwnd, (image_width, image_height), 'window too small',
                            generation, time.monotonic())

    # Grayscale matching is about three times faster than colour and enough for UI graphics
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    scale = find_scale(gray, templates, config)
    components = {}
    for component_type, names in config.anchor_templates.items():
        score, location, name, template = find_anchor(gray, templates, names, scale)
        if location is None or score < config.match_threshold:
            components[component_type] = DetectedComponent.missing(component_type, 'anchor not found')
            continue
        anchor = Region(location[0], location[1], template.shape[1], template.shape[0])
        region = derive_region(anchor, config.geometry[component_type], scale, (image_width, image_height))
        if region is None:
            components[component_type] = DetectedComponent.missing(component_type, 'region outside window')
            continue
        detail = {'anchor': anchor, 'template': name}
        if component_type is ComponentType.COMBAT_CONTROLS:
            detail['chase_on'] = name == names[0]
        components[component_type] = DetectedComponent(component_type, True, region, score, scale, detail)

    components[ComponentType.GAME_VIEW] = find_game_view(image, config)
    return Layout(window_hwnd, (image_width, image_height), components, scale, time.monotonic(), generation)


def recheck_layout(image, layout, templates, config):
    """ Re-matches found anchors near their known positions; returns the types that no longer match """
    check_image(image)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    failing = set()
    margin = round(config.recheck_margin * layout.scale)
    for component_type, component in layout.components.items():
        if not component.found or 'anchor' not in component.detail:
            continue
        anchor = component.detail['anchor']
        window = derive_region(anchor, (-margin, -margin, anchor.width + 2 * margin, anchor.height + 2 * margin),
                               1.0, gray.shape[1::-1])
        names = config.anchor_templates[component_type]
        score = 0.0
        if window is not None:
            score, _, _, _ = find_anchor(window.crop(gray), templates, names, layout.scale)
        if score < config.match_threshold:
            failing.add(component_type)
    return failing


class TemplateDetector:
    """ detect/recheck with templates loaded from images/ui/. Raises FileNotFoundError if any are missing """

    def __init__(self, config, templates=None):
        self.config = config
        self.templates = templates or Templates(config)

    def detect(self, image, window_hwnd=0, generation=0):
        return detect_layout(image, self.templates, self.config, window_hwnd, generation)

    def recheck(self, image, layout):
        return recheck_layout(image, layout, self.templates, self.config)
