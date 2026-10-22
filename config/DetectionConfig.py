from dataclasses import dataclass, field, fields

from detection.Components import ComponentType


# Anchor images in images/ui/ that locate each component. COMBAT_CONTROLS has two variants:
# which one matches tells whether chase mode is on.
ANCHOR_TEMPLATES = {
    ComponentType.HEALTH_BAR: ('heart.png',),
    ComponentType.MANA_BAR: ('mana.png',),
    ComponentType.BATTLE_LIST: ('battle_list_title.png',),
    ComponentType.MINIMAP: ('minimap_buttons.png',),
    ComponentType.COMBAT_CONTROLS: ('chase_on.png', 'chase_off.png'),
    ComponentType.STATUS_ICONS: ('status_strip.png',),
    ComponentType.CHAT: ('chat_tabs.png',),
}

# Templates searched inside a component rather than used as anchors
INNER_TEMPLATES = {
    'hunger': 'hunger.png',
}

# Component region relative to the anchor's top-left corner at scale 1.0: (dx, dy, width, height).
# A negative width or height means "the anchor's own width/height".
# Measure (T022): placeholders until measured on tests/testdata/client_*.png
GEOMETRY = {
    ComponentType.HEALTH_BAR: (14, 2, 90, 8),
    ComponentType.MANA_BAR: (14, 2, 90, 8),
    ComponentType.BATTLE_LIST: (0, 16, 170, 120),
    ComponentType.MINIMAP: (-112, 0, 106, 109),
    ComponentType.COMBAT_CONTROLS: (0, 0, -1, -1),
    ComponentType.STATUS_ICONS: (0, 0, -1, -1),
    ComponentType.CHAT: (0, -110, 300, 108),
}


@dataclass(frozen=True)
class DetectionConfig:
    """ Constants for finding the client and its components. Read values as attributes or with get() """
    # Measure (T022): confirm the executable name and title format on the target install
    title_prefix: str = 'Tibia'
    client_exe_name: str = 'client.exe'
    client_path_marker: str = 'tibia'

    templates_dir: str = 'images/ui'
    scales: tuple = (1.0, 1.25, 1.5, 1.75, 2.0)
    match_threshold: float = 0.85
    # Anchor used to find the common UI scale before the other anchors are matched
    scale_anchor: ComponentType = ComponentType.HEALTH_BAR
    anchor_templates: dict = field(default_factory=lambda: dict(ANCHOR_TEMPLATES))
    inner_templates: dict = field(default_factory=lambda: dict(INNER_TEMPLATES))
    geometry: dict = field(default_factory=lambda: dict(GEOMETRY))

    # A bar pixel counts as filled when both its HSV saturation and value reach these
    # Measure (T022)
    bar_fill_hsv: tuple = (80, 80)
    # Loot message colour in the chat, RGB, from the old config/Config.py
    # Measure (T022): confirm on the official client
    loot_colour: tuple = (240, 180, 0)
    # Battle list row height at scale 1.0 and the colour of the "targeted" frame, RGB
    # Measure (T022)
    battle_row_height: int = 22
    battle_target_colour: tuple = (255, 0, 0)
    battle_entry_colour: tuple = (0, 0, 0)

    game_view_aspect: float = 15 / 11
    aspect_tolerance: float = 0.03
    game_view_min_width: int = 150

    # Search margin, in pixels at scale 1.0, around a known anchor position when re-checking
    recheck_margin: int = 6

    def get(self, name):
        if name not in {f.name for f in fields(self)}:
            raise KeyError(name)
        return getattr(self, name)

    def template_files(self):
        """ Every anchor and inner template file name """
        names = [n for files in self.anchor_templates.values() for n in files]
        return names + list(self.inner_templates.values())
