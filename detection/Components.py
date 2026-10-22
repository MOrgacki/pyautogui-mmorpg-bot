from dataclasses import dataclass, field
from enum import Enum
from typing import Mapping


@dataclass(frozen=True)
class Region:
    """Axis-aligned rectangle in pixels"""
    x: int
    y: int
    width: int
    height: int

    def __post_init__(self):
        if self.width <= 0 or self.height <= 0:
            raise ValueError(f"Region needs a positive size, got {self.width}x{self.height}")

    @property
    def center(self):
        return (self.x + self.width // 2, self.y + self.height // 2)

    def contains(self, point):
        px, py = point
        return self.x <= px < self.x + self.width and self.y <= py < self.y + self.height

    def crop(self, image):
        """ Returns the part of a numpy image covered by this region """
        return image[self.y:self.y + self.height, self.x:self.x + self.width]

    def offset(self, dx, dy):
        return Region(self.x + dx, self.y + dy, self.width, self.height)

    def as_list(self):
        return [self.x, self.y, self.width, self.height]


class ComponentType(Enum):
    HEALTH_BAR = 'health bar'
    MANA_BAR = 'mana bar'
    BATTLE_LIST = 'battle list'
    MINIMAP = 'minimap'
    COMBAT_CONTROLS = 'combat controls'
    STATUS_ICONS = 'status icons'
    CHAT = 'chat'
    GAME_VIEW = 'game view'


@dataclass(frozen=True)
class DetectedComponent:
    type: ComponentType
    found: bool
    region: Region | None = None
    score: float = 0.0
    scale: float = 1.0
    detail: Mapping = field(default_factory=dict)
    missing_reason: str | None = None

    @staticmethod
    def missing(component_type, reason):
        return DetectedComponent(component_type, False, missing_reason=reason)


# The game view always shows 15x11 tiles and the character stands on the centre tile
GAME_VIEW_TILES = (15, 11)
CHARACTER_TILE = (7, 5)


@dataclass(frozen=True)
class Layout:
    """ Snapshot of every component of one client at one moment. Replaced, never edited """
    window_hwnd: int
    client_size: tuple
    components: Mapping
    scale: float = 1.0
    detected_at: float = 0.0
    generation: int = 0

    @staticmethod
    def empty(window_hwnd, client_size, reason, generation=0, detected_at=0.0):
        components = {t: DetectedComponent.missing(t, reason) for t in ComponentType}
        return Layout(window_hwnd, client_size, components, 1.0, detected_at, generation)

    def get(self, component_type):
        return self.components[component_type]

    def has(self, *component_types):
        return all(self.components[t].found for t in component_types)

    def missing(self, *component_types):
        """ Returns the given types that are not found, in the given order """
        return [t for t in component_types if not self.components[t].found]

    @property
    def tile_size(self):
        game_view = self.components[ComponentType.GAME_VIEW]
        if not game_view.found:
            raise KeyError(ComponentType.GAME_VIEW)
        return game_view.detail.get('tile_size', game_view.region.width / GAME_VIEW_TILES[0])

    def tile_point(self, dx, dy):
        """ Client point at the centre of the tile (dx, dy) away from the character """
        region = self.components[ComponentType.GAME_VIEW].region
        tile = self.tile_size
        x = region.x + (CHARACTER_TILE[0] + dx + 0.5) * tile
        y = region.y + (CHARACTER_TILE[1] + dy + 0.5) * tile
        return (round(x), round(y))
