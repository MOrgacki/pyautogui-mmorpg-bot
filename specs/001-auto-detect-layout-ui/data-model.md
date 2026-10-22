# Data Model: Auto-Detected Layout and Management UI

**Feature**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)

All coordinates are physical pixels (the process is DPI aware, see research R3). "Client
coordinates" are relative to the top-left of the client window's client area; "screen
coordinates" are on the virtual desktop. Only `ClientWindow.to_screen` converts between them.

## ClientWindow (`core/ClientWindow.py`)

One running official Tibia client.

| Field | Type | Rules |
|-------|------|-------|
| `hwnd` | int | Window handle; identity of the window for the session |
| `title` | str | Starts with the configured title prefix (default `Tibia`) |
| `pid` | int | Process id |
| `exe_path` | str | Must match the official client executable (R2); other clients are never created |
| `client_rect` | `Region` (screen coordinates) | Client area, excluding frame; width and height > 0 unless minimized |
| `state` | `WindowState` | `visible`, `minimized`, `lost` |
| `is_foreground` | bool | True when it is the foreground window |

- Identity: `hwnd`. The UI shows `title` (the character name is part of the title).
- `to_screen(point)`: client point → screen point using the current `client_rect`.
- `lost` when the handle no longer exists or the process exited.

## Region (`detection/Components.py`)

Immutable rectangle: `x`, `y`, `width`, `height` (int, width/height > 0), with `center`,
`contains(point)`, `crop(image)`, `offset(dx, dy)`.

## ComponentType (`detection/Components.py`)

Enum: `HEALTH_BAR`, `MANA_BAR`, `BATTLE_LIST`, `MINIMAP`, `COMBAT_CONTROLS`, `STATUS_ICONS`,
`CHAT`, `GAME_VIEW`.

## DetectedComponent (`detection/Components.py`)

| Field | Type | Rules |
|-------|------|-------|
| `type` | `ComponentType` | |
| `found` | bool | |
| `region` | `Region` or None | Client coordinates; None when not found |
| `score` | float | Match score 0–1; `found` requires score ≥ `match_threshold` |
| `scale` | float | Scale the anchor matched at (one of the configured scales) |
| `detail` | dict | Type-specific extras, e.g. `{"chase_on": True}` for `COMBAT_CONTROLS`, `{"tile_size": 32.0}` for `GAME_VIEW` |
| `missing_reason` | str or None | Set when not found, e.g. "anchor not found", "window too small" |

## Layout (`detection/Components.py`)

Immutable snapshot of all components for one client at one moment. Replaced whole on every
detection; never edited in place.

| Field | Type | Rules |
|-------|------|-------|
| `window_hwnd` | int | The client it was detected on |
| `client_size` | (int, int) | Client area size at detection time |
| `components` | dict[`ComponentType`, `DetectedComponent`] | One entry for every `ComponentType`, found or not |
| `scale` | float | Common UI scale |
| `detected_at` | float | Monotonic timestamp |
| `generation` | int | Increases by 1 on every new Layout; features use it to notice changes |

- `has(*types)`: True if all given types are found.
- `tile_point(dx, dy)`: client point of the tile at offset `(dx, dy)` from the character
  (`GAME_VIEW` required).
- Valid only while `client_size` equals the window's current client size; `LayoutMonitor`
  replaces it otherwise.

## Feature (`core/Supervisor.py` and `modules/*`)

One automated behaviour. Contract in [contracts/feature-interface.md](./contracts/feature-interface.md).

| Field | Type | Rules |
|-------|------|-------|
| `key` | str | Unique, stable: `healing`, `mana_refill`, `eating`, `attack_spells`, `chase`, `attack`, `loot`, `walk` |
| `label` | str | Shown in the UI |
| `requires(settings)` | frozenset[`ComponentType`] | Components needed to act; a method because eating's depend on settings |
| `enabled` | bool | User choice; persisted in Settings |
| `state` | `FeatureState` | See transitions |
| `pause_reason` | str or None | Set only in `paused` |

Required components per feature:

| Feature | Requires |
|---------|----------|
| `healing` | `HEALTH_BAR` |
| `mana_refill` | `MANA_BAR` |
| `eating` | none (interval mode); `STATUS_ICONS` when "eat when hungry" is on |
| `attack_spells` | `BATTLE_LIST` |
| `chase` | `COMBAT_CONTROLS` |
| `attack` | `BATTLE_LIST` |
| `loot` | `CHAT`, `GAME_VIEW`, `BATTLE_LIST` (a kill is the target frame disappearing) |
| `walk` | `MINIMAP`, `BATTLE_LIST` |

### FeatureState transitions

```text
            start                  required component missing / client not focused
   off ───────────────▶ running ─────────────────────────────────────────▶ paused(reason)
    ▲                     ▲  │                                                │
    │ stop                │  └─────────────── stop ──────────────┐            │
    │                     │                                      ▼            │
    │                     └──────── all required found again ── (any) ◀───────┘
    └───────────────────────────────────────────────────────── stop ─────────┘
```

- `off → running`: user starts the feature (or Start All with the feature enabled), a client is
  selected.
- `running → paused(reason)`: a required component is not found, the window is minimized or
  lost, or the client is not the foreground window. No input is sent while paused.
- `paused → running`: automatically, when the condition clears (FR-010).
- `running | paused → off`: user stops it; the task is cancelled within 1 s.
- `running → off` with an error log entry: the feature raised an unexpected exception; the
  Supervisor logs it and does not restart it automatically.

## Settings (`config/Settings.py`)

Everything the user can change. Schema in [contracts/settings-schema.md](./contracts/settings-schema.md).

| Group | Fields (defaults from today's code) |
|-------|-------------------------------------|
| `hotkeys` | `attack=f1`, `chase=f12`, `heal_high=f8`, `heal_low=f4`, `mana=f7`, `food=f5`, `spell_single=f2`, `spell_single_2=f3`, `spell_aoe=del`, `spell_aoe_strong=end`, `refresh_map=f6` |
| `healing` | `high_hp_percent=85`, `low_hp_percent=45` (low < high; both 1–99) |
| `mana` | `refill_below_percent=60` (1–99) |
| `eating` | `interval_min_s=20.3`, `interval_max_s=30.7` (min ≤ max, ≥ 1), `when_hungry=false` |
| `attack_spells` | `aoe_min_monsters=3` (2–8), `cooldown_min_s=2.3`, `cooldown_max_s=2.8` |
| `cavebot` | `route` (file name in `data/` or null), `arrival_radius_percent=6` (1–25) |
| `features` | `enabled`: map of feature key → bool, all false by default |
| `client` | `last_title` (str or null), used to pre-select a client when several are open |
| `version` | int, `1` |

- Validation runs on load and on every UI edit; an invalid value is rejected in the UI with a
  message and never applied.
- Values are percentages or seconds; no screen coordinates (FR-022).

## WaypointRoute (`Waypoints.py`)

Unchanged file format: `{"waypoints": ["images/marks/<name>.png", ...]}` in `data/`.

| Field | Type | Rules |
|-------|------|-------|
| `name` | str | File name in `data/` |
| `marks` | list[str] | At least one entry; each path must exist under `images/marks/` (validated on selection; invalid routes are shown as unusable) |
| `position` | int | Current index, wraps to 0 after the last mark |

## ActivityLogEntry (`core/ActivityLog.py`)

| Field | Type | Rules |
|-------|------|-------|
| `time` | float | Wall-clock timestamp |
| `source` | str | Feature key, or `detection`, `settings`, `supervisor` |
| `level` | str | `info`, `warning`, `error` |
| `message` | str | One line |

- In-memory ring buffer, last 500 entries; the UI shows the newest 100. Not persisted (matches
  the spec: a log of *recent* entries).

## StatusSnapshot (`core/Supervisor.py`)

Immutable object the UI reads every frame: list of client windows found, selected `hwnd`,
current `Layout` (or None), each feature's `state` and `pause_reason`, and the bot running flag.
Replaced atomically by the bot thread; the UI never mutates it.
