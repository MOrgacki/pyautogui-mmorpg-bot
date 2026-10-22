""" Synthetic client captures for detection tests until real fixtures exist (tasks T019-T021) """
import numpy as np

from config.DetectionConfig import DetectionConfig
from detection.Components import ComponentType
from detection.Templates import Templates, scale_image


C = ComponentType

TEMPLATE_SIZES = {
    'heart.png': (12, 12),
    'mana.png': (12, 12),
    'battle_list_title.png': (60, 14),
    'minimap_buttons.png': (20, 40),
    'chase_on.png': (22, 22),
    'chase_off.png': (22, 22),
    'status_strip.png': (100, 12),
    'chat_tabs.png': (80, 16),
    'hunger.png': (10, 10),
}

# Anchor top-left positions at scale 1.0 on an 800x600 client
POSITIONS_800 = {
    'heart.png': (520, 380),
    'mana.png': (520, 400),
    'battle_list_title.png': (600, 10),
    'minimap_buttons.png': (720, 160),
    'chase_on.png': (520, 300),
    'status_strip.png': (520, 340),
    'chat_tabs.png': (10, 560),
}

GAME_VIEW_800 = (10, 10, 480, 352)
GAME_VIEW_1920 = (10, 10, 1050, 770)


def make_templates(seed=7):
    rng = np.random.default_rng(seed)
    images = {}
    for name, (width, height) in TEMPLATE_SIZES.items():
        images[name] = rng.integers(0, 256, (height, width, 3), dtype=np.uint8)
    return images


def make_client(size=(800, 600), scale=1.0, omit=(), chase='chase_on.png', seed=7, offset=(0, 0)):
    """ Returns (image, templates, anchors) with anchors as {file name: (x, y, w, h)} """
    images = make_templates(seed)
    rng = np.random.default_rng(seed + 1)
    width, height = size
    image = np.full((height, width, 3), 70, np.uint8)
    image += rng.integers(0, 3, image.shape, dtype=np.uint8)

    game_view = GAME_VIEW_800 if size == (800, 600) else GAME_VIEW_1920
    gx, gy, gw, gh = game_view
    # 2 px black frame exactly on the game view's outer edge
    image[gy:gy + gh, gx:gx + gw] = 0
    image[gy + 2:gy + gh - 2, gx + 2:gx + gw - 2] = 120

    positions = dict(POSITIONS_800)
    if chase != 'chase_on.png':
        positions[chase] = positions.pop('chase_on.png')
    anchors = {}
    for name, (x, y) in positions.items():
        if name in omit:
            continue
        x, y = x + offset[0], y + offset[1]
        template = scale_image(images[name], scale)
        th, tw = template.shape[:2]
        image[y:y + th, x:x + tw] = template
        anchors[name] = (x, y, tw, th)
    return image, Templates(DetectionConfig(), images), anchors, game_view


def expected_region(anchor, component_type, scale, config=DetectionConfig()):
    ax, ay, aw, ah = anchor
    dx, dy, width, height = config.geometry[component_type]
    width = aw if width < 0 else round(width * scale)
    height = ah if height < 0 else round(height * scale)
    return (ax + round(dx * scale), ay + round(dy * scale), width, height)


def make_bar(percent, width=100, height=8, colour=(0, 200, 0)):
    """ BGR bar filled from the left with a saturated colour; the rest dark grey """
    bar = np.full((height, width, 3), 40, np.uint8)
    filled = round(width * percent / 100)
    bar[:, :filled] = colour
    return bar


def make_battle(count, targeted=False, rows=6, row_height=22, width=170):
    """ BGR battle list: each entry draws a black health-bar frame; the target gets a red frame """
    image = np.full((rows * row_height, width, 3), 90, np.uint8)
    for row in range(count):
        top = row * row_height
        image[top + 15:top + 17, 30:120] = 0
    if targeted and count:
        image[0:row_height, 0:2] = (0, 0, 255)
    return image


def make_minimap(mark, at=None, size=(106, 109), seed=3):
    """ BGR minimap of smooth noise with a mark pasted at its centre point 'at' (None = no mark) """
    rng = np.random.default_rng(seed)
    width, height = size
    image = (rng.integers(40, 60, (height, width, 3), dtype=np.uint8))
    if at is not None:
        mh, mw = mark.shape[:2]
        x, y = at[0] - mw // 2, at[1] - mh // 2
        image[y:y + mh, x:x + mw] = mark
    return image
