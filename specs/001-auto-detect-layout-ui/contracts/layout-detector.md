# Contract: Layout Detection and Readers

Pure functions in `detection/`. No screen capture, window or input access; inputs are images
and config, outputs are values. This is what makes Principle IV testable.

## `detect_layout`

```python
def detect_layout(
    image: np.ndarray,            # BGR capture of the client area, any size
    templates: Templates,         # loaded once from images/ui/
    config: DetectionConfig,
    window_hwnd: int = 0,
    generation: int = 0,
) -> Layout
```

- Returns a `Layout` with an entry for **every** `ComponentType`; components that are not found
  have `found=False` and a `missing_reason`. Never raises because a component is missing.
- Raises `ValueError` only for an invalid input image (empty, not 3-channel).
- All regions are in client coordinates (relative to `image`).
- Deterministic: the same image gives the same Layout.
- Time budget: under 1 s for a 1920x1080 image.

Errors and edge cases:

| Input | Result |
|-------|--------|
| Image smaller than the smallest anchor at scale 1.0 | All components `found=False`, reason `window too small` |
| Battle list closed in the client | `BATTLE_LIST.found=False`, reason `anchor not found`; others unaffected |
| Two candidates for one anchor | Highest score wins; tie broken by top-most, then left-most |
| No 15:11 rectangle | `GAME_VIEW.found=False`, reason `game view not found` |

## `recheck_layout`

```python
def recheck_layout(image: np.ndarray, layout: Layout, templates: Templates,
                   config: DetectionConfig) -> set[ComponentType]
```

Re-matches each found component's anchor only at its known position and scale. Returns the
types that no longer match. Used by `LayoutMonitor` every 2 s (research R10).

## Readers (`detection/Readers.py`)

| Function | Input | Output | Invalid input |
|----------|-------|--------|---------------|
| `bar_percent(image)` | Crop of `HEALTH_BAR` or `MANA_BAR` | float 0–100 | `ValueError` for an empty crop |
| `battle_entries(image, scale)` | Crop of `BATTLE_LIST` | `BattleState(count: int, targeted: bool)` | — |
| `chase_on(layout)` | `Layout` | bool | `KeyError` if `COMBAT_CONTROLS` not found |
| `hunger_present(image, templates, scale)` | Crop of `STATUS_ICONS` | bool | — |
| `loot_message_present(image, colour)` | Crop of `CHAT` | bool | — |
| `find_mark(image, mark, scale, threshold)` | Crop of `MINIMAP`, mark image | `(x, y)` relative to the crop, or None | — |
| `is_arrived(point, minimap_size, radius_percent)` | point from `find_mark` | bool | — |

## Templates (`detection/Templates.py`)

- Loads every PNG listed in `DetectionConfig.anchor_templates` from `images/ui/` once.
  A missing file raises `FileNotFoundError` naming the file, at application start, not during
  a feature pass.
- Caches resized variants per scale.
- Waypoint marks from `images/marks/` are loaded on route selection and cached the same way.

## `DetectionConfig` (`config/DetectionConfig.py`)

Holds, as named constants with typed accessors: `title_prefix`, `client_exe_name`,
`scales`, `match_threshold`, `anchor_templates` (component → file names), anchor-relative
`geometry` (component → offset/size at scale 1.0), `bar_fill_hsv`, `loot_colour`,
`game_view_aspect` (15/11) and `aspect_tolerance` (0.03). Accessing an unknown name raises
`KeyError`.

## Test obligations

Each function above has tests in `tests/test_LayoutDetector.py` or `tests/test_Readers.py`
using fixtures in `tests/testdata/`. `detect_layout` is tested on at least
`client_800x600.png` and `client_1920x1080.png`, with expected regions stored as JSON next to
the fixture (`client_800x600.expected.json`) and compared within 3 px.
