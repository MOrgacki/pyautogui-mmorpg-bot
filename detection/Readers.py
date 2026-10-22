""" Pure functions that turn a component capture (BGR array) into a value """
import math
from dataclasses import dataclass

import cv2
import numpy as np

from config.DetectionConfig import DetectionConfig
from detection.Components import ComponentType
from detection.LayoutDetector import match_template


def _check(image):
    if image is None or image.size == 0:
        raise ValueError('empty component image')


def bar_percent(image, config=DetectionConfig()):
    """ Fill of a health or mana bar, 0-100, from its middle row (research R7) """
    _check(image)
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    row = hsv[hsv.shape[0] // 2]
    min_saturation, min_value = config.bar_fill_hsv
    filled = (row[:, 1] >= min_saturation) & (row[:, 2] >= min_value)
    width = len(filled)
    # The fill starts at the left edge; allow a thin border before it
    start_limit = max(1, math.ceil(width * 0.05))
    starts = np.flatnonzero(filled[:start_limit])
    if starts.size == 0:
        return 0.0
    start = starts[0]
    gaps = np.flatnonzero(~filled[start:])
    end = start + (gaps[0] if gaps.size else width - start)
    return min(100.0, end / width * 100.0)


@dataclass(frozen=True)
class BattleState:
    count: int
    targeted: bool


def _colour_mask(image, rgb):
    return np.all(image == np.array(rgb[::-1], dtype=image.dtype), axis=-1)


def battle_entries(image, scale=1.0, config=DetectionConfig()):
    """ Monster rows in the battle list and whether one of them is targeted """
    _check(image)
    row_height = max(1, round(config.battle_row_height * scale))
    entry_pixels = _colour_mask(image, config.battle_entry_colour)
    count = 0
    for top in range(0, image.shape[0] - row_height + 1, row_height):
        # An entry draws a black health-bar frame; an empty row draws none
        if entry_pixels[top:top + row_height].sum() >= 10:
            count += 1
        else:
            break
    targeted = bool(_colour_mask(image, config.battle_target_colour).any())
    return BattleState(count, targeted and count > 0)


def chase_on(layout):
    component = layout.get(ComponentType.COMBAT_CONTROLS)
    if not component.found:
        raise KeyError(ComponentType.COMBAT_CONTROLS)
    return bool(component.detail['chase_on'])


def chase_state(image, on_template, off_template):
    """ Live chase state from a capture of the chase button: True, False, or None if neither matches """
    _check(image)
    on_score, on_location = match_template(image, on_template)
    off_score, off_location = match_template(image, off_template)
    if on_location is None and off_location is None:
        return None
    if max(on_score, off_score) < DetectionConfig().match_threshold:
        return None
    return on_score >= off_score


def hunger_present(image, hunger_template, threshold=DetectionConfig().match_threshold):
    _check(image)
    score, location = match_template(image, hunger_template)
    return location is not None and score >= threshold


def loot_message_present(image, colour=DetectionConfig().loot_colour):
    """ Any pixel in the loot message colour (RGB) """
    _check(image)
    return bool(_colour_mask(image, colour).any())


def find_mark(image, mark, threshold=DetectionConfig().match_threshold):
    """ Centre of a waypoint mark inside the minimap image, or None """
    _check(image)
    score, location = match_template(image, mark)
    if location is None or score < threshold:
        return None
    return (location[0] + mark.shape[1] // 2, location[1] + mark.shape[0] // 2)


def is_arrived(point, minimap_size, radius_percent):
    """ True when a minimap point is within radius_percent of the minimap width from its centre """
    width, height = minimap_size
    distance = math.hypot(point[0] - width / 2, point[1] - height / 2)
    return distance <= width * radius_percent / 100
