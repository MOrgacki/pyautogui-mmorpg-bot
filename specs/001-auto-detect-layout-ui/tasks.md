---

description: "Task list for Auto-Detected Layout and Management UI"
---

# Tasks: Auto-Detected Layout and Management UI

**Input**: Design documents from `specs/001-auto-detect-layout-ui/`

**Prerequisites**: [plan.md](./plan.md), [spec.md](./spec.md), [research.md](./research.md),
[data-model.md](./data-model.md), [contracts/](./contracts/), [quickstart.md](./quickstart.md)

**Tests**: Included. Constitution Principle IV requires `unittest` tests with fixtures for all
new or changed detection and analysis logic, at two or more resolutions. Write each story's
tests first and confirm they fail before implementing.

**Organization**: Tasks are grouped by user story so each story can be built and tested on its
own.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: The user story the task belongs to (US1–US4)
- **MANUAL**: Needs a person with the official Tibia client running; cannot be done by an agent

## Path Conventions

Single desktop project at the repository root (see plan.md "Project Structure"): `core/`,
`detection/`, `config/`, `modules/`, `ui/`, `helpers/`, `images/`, `tests/`. All commands run
from the repository root. New modules follow the existing convention: lowercase package
directories, one class per CapitalCase file.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Dependencies and package skeleton

- [X] T001 Create `requirements.txt` pinning the newest releases with Python 3.13 wheels of `dearpygui` (2.x), `opencv-python`, `numpy` (2.x), `mss`, `pywin32`, `psutil`, `pyautogui`, `Pillow` (research R14), then run `python -m pip install -r requirements.txt` and confirm every package imports
- [X] T002 [P] Add `settings.json`, `settings.json.tmp` and `settings.json.bad` to `.gitignore`
- [X] T003 [P] Create empty packages `core/__init__.py`, `detection/__init__.py`, `ui/__init__.py` and the directory `images/ui/` (with a `.gitkeep`)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Data types, settings, window/capture/input access, the bot thread, and the empty UI
shell that every story builds on

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

### Tests for the foundation

- [X] T004 [P] Write `tests/test_Components.py`: `Region.contains`, `Region.crop` on a numpy array, `Region.offset`, `Region.center`; `Layout.has(...)` true only when every listed type is found; `Layout.tile_point(dx, dy)` returns the tile centre for a `GAME_VIEW` region of 480x352 at tile size 32 (character tile is column 7, row 5, counting from 0)
- [X] T005 [P] Write `tests/test_Settings.py` covering contracts/settings-schema.md: missing file → defaults with no warning; save → load round trip; invalid JSON → file renamed to `settings.json.bad`, defaults used, warning returned; one invalid field (e.g. `healing.low_hp_percent = 120`) → that field defaulted, others kept; `low_hp_percent >= high_hp_percent` rejected; unknown key ignored with warning; misspelt attribute access raises `AttributeError`. Use a temp directory, never the real `settings.json`
- [X] T006 [P] Write `tests/test_ClientWindow.py` using injected fake window lists: official client (`title "Tibia - Knight"`, exe `...\Tibia\packages\Tibia\bin\client.exe`) accepted; browser tab titled `Tibia - Wiki` in `chrome.exe` rejected; OpenTibia client window rejected; invisible window rejected; minimized window gets `state == minimized`; vanished handle gets `state == lost`
- [X] T007 [P] Write `tests/test_Supervisor.py` (part 1) with a fake feature and no real window: `start_feature` runs it on the bot thread; `stop_feature` cancels it and its state is `off` within 1 s; `stop_all` stops every feature within 1 s; a feature that raises `RuntimeError` ends as `off` with an `error` entry in the activity log; `apply_settings` makes the new `Settings` visible to the feature on its next pass

### Implementation

- [X] T008 [P] Implement `detection/Components.py` per data-model.md: frozen dataclasses `Region` (`x`, `y`, `width`, `height` ints, "width/height > 0", with `center`, `contains`, `crop`, `offset`), enum `ComponentType` (`HEALTH_BAR`, `MANA_BAR`, `BATTLE_LIST`, `MINIMAP`, `COMBAT_CONTROLS`, `STATUS_ICONS`, `CHAT`, `GAME_VIEW`), `DetectedComponent` (`type`, `found`, `region` or None, `score` 0–1, `scale`, `detail` dict, `missing_reason`), and `Layout` (`window_hwnd`, `client_size`, `components` with "one entry for every `ComponentType`, found or not", `scale`, `detected_at`, `generation`, plus `has()` and `tile_point()`)
- [X] T009 [P] Implement `config/DetectionConfig.py` per contracts/layout-detector.md: named constants `title_prefix="Tibia"`, `client_exe_name="client.exe"`, `scales=(1.0, 1.25, 1.5, 1.75, 2.0)`, `match_threshold=0.85`, `anchor_templates` (component → file names in `images/ui/`), `geometry` (component → anchor-relative offset and size at scale 1.0), `bar_fill_hsv`, `loot_colour=(240, 180, 0)` (RGB, from today's `config/Config.py`), `game_view_aspect=15/11`, `aspect_tolerance=0.03`, `arrival_radius_default=6`; a `get(name)` accessor that raises `KeyError` for an unknown name. Geometry and colour values that research.md marks **Measure** start as clearly named placeholders with a `# Measure (T022)` comment
- [X] T010 [P] Implement `config/Settings.py`: frozen dataclasses `Hotkeys`, `HealingSettings`, `ManaSettings`, `EatingSettings`, `AttackSpellSettings`, `CaveBotSettings`, `FeatureSettings`, `ClientSettings`, `Settings` with the defaults and validation rules in contracts/settings-schema.md (e.g. "Integers 1–99, `low < high`"; "Numbers ≥ 1, `min ≤ max`"; "Integer 2–8"; hotkeys checked against `pyautogui.KEYBOARD_KEYS` lower-cased); `SettingsStore(path="./settings.json")` with `load() -> (Settings, list[str] warnings)` and `save(settings)` writing `settings.json.tmp` then `os.replace` (makes T005 pass)
- [X] T011 [P] Implement `core/ActivityLog.py`: thread-safe (`threading.Lock`) ring buffer of `ActivityLogEntry(time, source, level, message)` holding the last 500 entries, with `add(source, message, level="info")` and `entries(limit=100, source=None)` newest first
- [X] T012 [P] Implement `core/ClientWindow.py`: `WindowState` enum (`visible`, `minimized`, `lost`); `ClientWindow` dataclass (`hwnd`, `title`, `pid`, `exe_path`, `client_rect` as a screen-coordinate `Region` from `GetClientRect` + `ClientToScreen`, `state`, `is_foreground`) with `refresh()` and `to_screen(point)`; `find_client_windows(config, enum_windows=..., exe_of_pid=...)` using `win32gui.EnumWindows`, `win32process.GetWindowThreadProcessId` and `psutil.Process(pid).exe()`, keeping only visible windows whose title starts with `title_prefix` and whose exe file name is `client_exe_name` inside a path containing `Tibia` (research R2). Injectable functions make T006 pass without real windows
- [X] T013 [P] Implement `core/ScreenCapture.py`: lazily created `mss.mss()` (none in the constructor, Principle IV); `capture_client(window) -> np.ndarray` (BGR) of `window.client_rect`; `capture_region(window, region) -> np.ndarray` for a client-coordinate `Region`
- [X] T014 Implement `core/GameInput.py` (depends on T012): `press(window, key) -> bool` and `click(window, client_point, button="left", modifier=None) -> bool` that return False and send nothing unless `window.is_foreground` after a fresh `refresh()`; clicks convert with `window.to_screen`; keep `pyautogui.FAILSAFE = True`; keep today's random 0.1–0.2 s delay after a key press (from `helpers/Helpers.py`) but as `await`-able `async` variants `press_async`/`click_async` using `asyncio.sleep`
- [X] T015 Implement `core/Supervisor.py` (depends on T008, T010, T011, T013, T014) per contracts/feature-interface.md: a daemon thread running one asyncio event loop; the `Feature` protocol (`key`, `label`, `requires`, `async run(ctx)`); `FEATURE_REQUIREMENTS` registry mapping the 8 feature keys to the required components table in data-model.md; `FeatureContext` exposing `layout`, `settings`, `ready()`, `capture()`, `press()`, `click()`, `report_mismatch()`, `log()` (for now `ready()` only waits until a client is selected); thread-safe `select_client(hwnd)`, `register(feature)`, `start_feature(key)`, `stop_feature(key)`, `start_all()`, `stop_all()`, `apply_settings(settings)` via `loop.call_soon_threadsafe`; each feature as its own `asyncio.Task`, cancelled on stop; unexpected exceptions logged as `error` and the feature set to `off`; an immutable `StatusSnapshot` (clients, selected hwnd, layout, feature states and pause reasons, running flag) replaced atomically after every change (makes T007 pass)
- [X] T016 Implement `ui/MainWindow.py` shell with Dear PyGui 2.x (depends on T015) per contracts/ui-controls.md "Header": always-on-top resizable viewport 420x560; client selector combo, client status text, Start All / Stop All button; empty tabs Run, Detection, Settings, Log; reads `StatusSnapshot` once per frame in a manual render loop (`while dpg.is_dearpygui_running(): ...; dpg.render_dearpygui_frame()`); callbacks only call Supervisor methods
- [X] T017 Rewrite `App.py` (depends on T010, T015, T016): first statements set per-monitor DPI awareness through `ctypes.windll.shcore.SetProcessDpiAwareness(2)` with a fallback to `ctypes.windll.user32.SetProcessDPIAware()`, before importing `pyautogui`, `mss` or `dearpygui` (research R3); then load settings with `SettingsStore`, create the `Supervisor`, run `MainWindow`; on window close call `stop_all()` and wait up to 2 s. Remove the old Dear PyGui 0.x code and the module-level `should_*` globals
- [X] T018 [P] Implement `helpers/CaptureClient.py` (depends on T012, T013): `python helpers/CaptureClient.py <output.png>` finds official clients, picks the only one (or the one whose title contains an optional `--title` argument), sets DPI awareness like `App.py`, and saves its client-area capture as PNG

**Checkpoint**: `python -m unittest discover -v -s ./tests -p "test_*.py"` passes T004–T007; `python App.py` opens the empty control window and lists running official clients

---

## Phase 3: User Story 1 - Bot finds the game window and its components by itself (Priority: P1) 🎯 MVP

**Goal**: With no calibration, the bot finds the official client at any window size and reports
where each component is, with a preview.

**Independent Test**: Open the client at two window sizes, press Detect now, and confirm the
Detection tab shows the window and every component as found, with outlines over the right parts
(quickstart steps 1–3).

### Fixtures and reference images for User Story 1

- [ ] T019 [US1] MANUAL: with `helpers/CaptureClient.py`, capture the official client (default layout, battle list open with at least one monster, minimap showing a route mark, health and mana not full) to `tests/testdata/client_800x600.png`, `tests/testdata/client_1920x1080.png` (maximized), `tests/testdata/client_1920x1080_no_battle_list.png` (battle list closed) and `tests/testdata/client_1920x1080_125.png` (Windows display scaling 125%)
- [ ] T020 [US1] MANUAL: crop anchor templates from `tests/testdata/client_1920x1080.png` into `images/ui/`: `heart.png`, `mana.png`, `battle_list_title.png`, `minimap_buttons.png`, `chase_on.png`, `chase_off.png` (capture a second screenshot with chase toggled if needed), `status_strip.png`, `hunger.png` (from a capture while hungry), `chat_tabs.png`. Use `helpers/QuickSS.py` or an image editor; crop tightly with no game-view pixels
- [ ] T021 [US1] MANUAL: write `tests/testdata/client_800x600.expected.json`, `client_1920x1080.expected.json`, `client_1920x1080_no_battle_list.expected.json` and `client_1920x1080_125.expected.json`, each mapping every `ComponentType` name to `{"found": bool, "region": [x, y, w, h]}` measured by hand, plus `"health_percent"`, `"mana_percent"`, `"battle_count"`, `"battle_targeted"` and `"chase_on"` as seen in the screenshot (used by US2 and US3 reader tests)
- [ ] T022 [US1] Measure and fill every `# Measure (T022)` placeholder in `config/DetectionConfig.py` from the fixtures: anchor-relative offset and size of each component region at scale 1.0, bar fill HSV thresholds, the confirmed `client_exe_name` and title format, and the loot message colour; remove the placeholder comments

### Tests for User Story 1 ⚠️ write first, confirm they fail

- [X] T023 [P] [US1] Write `tests/test_LayoutDetector.py` per contracts/layout-detector.md: for `client_800x600`, `client_1920x1080` and `client_1920x1080_125`, every component found and each region within 3 px of the expected JSON; for `client_1920x1080_no_battle_list`, `BATTLE_LIST.found == False` with reason `anchor not found` and all other components found; a 100x100 image gives every component `found=False` with reason `window too small`; an empty or 1-channel image raises `ValueError`; two runs on the same image give equal Layouts; detection on `client_1920x1080.png` takes under 1 s; `recheck_layout` returns an empty set on the same image and `{BATTLE_LIST}` when given the no-battle-list image with the full Layout
- [X] T024 [P] [US1] Write `tests/test_Templates.py`: all files in `DetectionConfig.anchor_templates` load; a missing file raises `FileNotFoundError` naming the file; the scaled variant at 1.5 is 1.5x the size (±1 px)

### Implementation for User Story 1

- [X] T025 [P] [US1] Implement `detection/Templates.py`: load every PNG in `DetectionConfig.anchor_templates` from `images/ui/` once as BGR arrays, raise `FileNotFoundError` naming a missing file, cache `cv2.resize` variants per scale (`INTER_AREA` for down, `INTER_LINEAR` for up); `load_mark(path)` for waypoint marks with the same cache (makes T024 pass)
- [X] T026 [US1] Implement anchor detection in `detection/LayoutDetector.py` `detect_layout(image, templates, config, window_hwnd=0, generation=0)` (depends on T022, T025): validate the image (`ValueError` if empty or not 3-channel); find the best scale with the first anchor (`heart.png`) over `config.scales` using `cv2.matchTemplate(..., cv2.TM_CCOEFF_NORMED)`; match every other anchor at that scale; a match is found when score ≥ `match_threshold`; ties go to top-most then left-most; derive each region from the anchor box plus `geometry` x scale, clipped to the image; for `COMBAT_CONTROLS` match both `chase_on` and `chase_off` and store `detail["chase_on"]`; for `STATUS_ICONS` the region is the strip; images smaller than the smallest anchor give every component `found=False`, reason `window too small`; always return an entry for every `ComponentType`
- [X] T027 [US1] Add game view detection to `detection/LayoutDetector.py` (depends on T026): `cv2.Canny` + `cv2.findContours`, keep axis-aligned rectangles whose aspect ratio is within `aspect_tolerance` of 15:11, pick the largest, ignore black letterbox bars; set `detail["tile_size"] = width / 15`; if none, `GAME_VIEW.found=False` with reason `game view not found`
- [X] T028 [US1] Implement `recheck_layout(image, layout, templates, config) -> set[ComponentType]` in `detection/LayoutDetector.py`: re-match each found component's anchor only in a small window around its known position at `layout.scale`; return the types whose score fell below `match_threshold` (makes T023 pass)
- [X] T029 [US1] Add detection to `core/Supervisor.py`: `detect_now()` (thread-safe) captures the selected client on the bot thread, runs `detect_layout` in `loop.run_in_executor` so the loop keeps serving features, stores the new `Layout` with `generation + 1`, the capture and the duration in `StatusSnapshot`, and logs `detection` entries for each component that changed between found and missing; refresh `find_client_windows` every 1 s into the snapshot; auto-select when exactly one client is found, pre-select the one matching `settings.client.last_title`, and select none when several are found and none matches
- [X] T030 [P] [US1] Implement `ui/DetectionPreview.py`: turn the last capture (BGR numpy) into a Dear PyGui dynamic texture scaled to fit the tab width, draw a rectangle and label per found component with a drawlist; refresh only when the Layout `generation` changes or Detect now is pressed
- [X] T031 [US1] Build the Detection tab and client selector in `ui/MainWindow.py` (depends on T029, T030) per contracts/ui-controls.md: client combo lists titles, shows "No Tibia client found" and disables Start All when there are none, selecting a client calls `select_client` and saves `client.last_title`; client status `Found` / `Minimized` / `Not focused` / `Lost`; component table (Found/Missing, reason, score, region size, and the features from `FEATURE_REQUIREMENTS` that need each missing component); Detect now button; preview; last detection time and duration

**Checkpoint**: Tests T023–T024 pass; quickstart steps 1–3 behave as described at two window sizes

---

## Phase 4: User Story 2 - Features keep working when the window changes (Priority: P1)

**Goal**: Re-detect on move/resize/restore, pause any feature whose components are missing or
whose client is not focused, and resume automatically. Proven with Healing and Mana refill.

**Independent Test**: Start Healing, resize the client and confirm it still heals at the
threshold; cover the health bar and confirm it pauses with a reason and presses nothing
(quickstart steps 4–8).

### Tests for User Story 2 ⚠️ write first, confirm they fail

- [X] T032 [P] [US2] Write `tests/test_Readers.py` (part 1): `bar_percent` on the `HEALTH_BAR` and `MANA_BAR` crops of `client_800x600.png`, `client_1920x1080.png` and `client_1920x1080_125.png` (regions from the expected JSON) is within ±3 of `health_percent` / `mana_percent`; a fully dark synthetic bar gives 0; a fully filled one gives 100; an empty crop raises `ValueError`
- [X] T033 [P] [US2] Write `tests/test_LayoutMonitor.py` with a fake window whose `client_rect` changes and a fake detector: a rect change triggers exactly one re-detection after the 0.3 s settle delay even when the rect changes 5 times within it; minimized → no detection, state reported; restored → re-detection; `report_mismatch` triggers re-detection; periodic `recheck_layout` every 2 s marks components missing without a full detection
- [X] T034 [P] [US2] Extend `tests/test_Supervisor.py` (part 2) with a fake `GameInput` that records calls: a feature requiring `HEALTH_BAR` is `paused` with reason `health bar not found` and records zero presses while the Layout lacks it; becomes `running` within 1 s of a Layout that has it; window not foreground → `paused` with reason `client not focused`; window minimized or lost → every running feature paused
- [X] T035 [P] [US2] Write `tests/test_Healing.py` with a fake `FeatureContext`: HP below `low_hp_percent` presses `heal_low`; between low and high presses `heal_high`; above high presses nothing; `ManaRefillFeature` presses `mana` below `refill_below_percent`; while `mana_refill` is running and mana is below its threshold, `HealingFeature` skips its pass; with `mana_refill` off, healing heals regardless of mana; a bar reading outside 0–100 calls `report_mismatch` and presses nothing; settings changed between passes are used on the next pass

### Implementation for User Story 2

- [X] T036 [P] [US2] Implement `bar_percent(image) -> float` in `detection/Readers.py` per research R7: scan the middle row; a pixel is filled when its HSV saturation and value exceed `DetectionConfig.bar_fill_hsv`; percent = longest filled run from the left / width x 100; `ValueError` on an empty crop (makes T032 pass)
- [X] T037 [US2] Implement `core/LayoutMonitor.py` per research R10 (depends on T028, T029): an async loop on the bot thread that every 0.25 s refreshes the selected `ClientWindow`; after a rect change waits 0.3 s for it to settle, then calls the Supervisor's detection; re-detects on restore and on `report_mismatch`; every 2 s runs `recheck_layout` and publishes a Layout with failing components set to `found=False`, reason `component stopped matching`; sets an `asyncio.Event` `layout_changed` on every new Layout; detection and `await asyncio.sleep` on every path (Principle I) (makes T033 pass)
- [X] T038 [US2] Complete `FeatureContext.ready()` in `core/Supervisor.py` (depends on T037): loop until the client is selected, `visible`, foreground, and `layout.has(*feature.requires)`; while not, set the feature state to `paused` with a reason (`no client selected`, `client minimized`, `client lost`, `client not focused`, or `<component> not found` in lower case words) and wait on `layout_changed` with a 0.5 s timeout; on success set it back to `running`; log every pause and resume; route `press`/`click` through `GameInput` and treat a refused input as a pause with reason `client not focused`; `report_mismatch` forwards to `LayoutMonitor` (makes T034 pass)
- [X] T039 [US2] Rewrite `modules/Healing.py` as `HealingFeature` (`key="healing"`, `requires={HEALTH_BAR}`) and `ManaRefillFeature` (`key="mana_refill"`, `requires={MANA_BAR}`) per contracts/feature-interface.md: each pass `await ctx.ready()`, capture the bar, `bar_percent`, compare with `ctx.settings` (read every pass), press via `ctx.press`, then `await asyncio.sleep(0.05)`; implement the mana-priority rule; no `config.PixelConfig` / `KeysConfig` / `ImageProcessingConfig` imports (makes T035 pass)
- [X] T040 [US2] Register `HealingFeature` and `ManaRefillFeature` in `App.py` and add the Run tab feature rows to `ui/MainWindow.py`: Enabled checkbox (saved to `features.enabled`), name, and State (`Off`, `Running`, `Paused: <reason>`); Start All starts the enabled features

**Checkpoint**: Tests T032–T035 pass; quickstart steps 4–8 behave as described; US1 still works

---

## Phase 5: User Story 3 - Manage everything from the UI (Priority: P2)

**Goal**: Start and stop each feature on its own, edit and save every setting, choose a route,
and run all eight features on detected positions (FR-025).

**Independent Test**: Start Healing and Eating, stop only Eating, change the healing threshold
and a hotkey, restart the app, and confirm both changes were kept and Eating is off; walk a
route with attack and loot (quickstart steps 9–12, 14).

### Tests for User Story 3 ⚠️ write first, confirm they fail

- [X] T041 [P] [US3] Extend `tests/test_Readers.py` (part 2): `battle_entries` on the `BATTLE_LIST` crops of the 800x600 and 1920x1080 fixtures returns `battle_count` and `battle_targeted` from the expected JSON; `chase_on(layout)` matches `chase_on`; `hunger_present` true on the hungry capture from T020 and false on `client_1920x1080.png`; `loot_message_present` true on `tests/testdata/loot_found.png` and false on `tests/testdata/empty_loot.png`; `find_mark` finds the route mark in the `MINIMAP` crop at both sizes and returns None for a mark not on the map; `is_arrived` true within `arrival_radius_percent` of the centre and false outside
- [X] T042 [P] [US3] Rewrite `tests/test_CaveBot.py` with a fake `FeatureContext`: `AttackFeature` presses `attack` when the battle list has an untargeted monster and waits while targeted; `LootFeature` shift+right-clicks the 9 tiles from `layout.tile_point(dx, dy)` for `dx, dy in -1..1` when the loot message is present, and releases Shift even when cancelled mid-loop; `WalkFeature` clicks the current mark, advances on arrival, wraps to the first mark after the last, and on "mark not found" presses `refresh_map` once and logs it; no bare `except:` in `modules/CaveBot.py` (assert with `ast`). Keep the existing loot fixture tests, now through `loot_message_present`
- [X] T043 [P] [US3] Write `tests/test_Utils.py` and `tests/test_AttackSpells.py` with a fake `FeatureContext`: `EatingFeature` presses `food` and sleeps a value in `[interval_min_s, interval_max_s]`; with `when_hungry` it presses only when `hunger_present`; `ChaseFeature` presses `chase` only when chase is off; `AttackSpellsFeature` uses single-target spells below `aoe_min_monsters` and AoE spells at or above it, only when a monster is targeted, then sleeps within the cooldown range
- [X] T044 [P] [US3] Write `tests/test_Waypoints.py`: every file in `data/` loads; a route listing a missing mark image is reported invalid with the missing path; the `{"waypoints": [...]}` format is unchanged

### Implementation for User Story 3

- [X] T045 [US3] Implement the remaining readers in `detection/Readers.py` per contracts/layout-detector.md: `battle_entries(image, scale) -> BattleState(count, targeted)`, `chase_on(layout)` (`KeyError` if `COMBAT_CONTROLS` not found), `hunger_present(image, templates, scale)`, `loot_message_present(image, colour)` (any pixel equal to `loot_colour`, matching today's `check_loot_area`), `find_mark(image, mark, scale, threshold)` returning a crop-relative point or None, `is_arrived(point, minimap_size, radius_percent)` (makes T041 pass)
- [X] T046 [P] [US3] Rewrite `modules/Utils.py` as `EatingFeature` (`key="eating"`, `requires` empty, or `{STATUS_ICONS}` when `when_hungry`) and `ChaseFeature` (`key="chase"`, `requires={COMBAT_CONTROLS}`) per the feature contract; every pass awaits (today's `auto_chase` loop does not await when it presses; fix that) (makes T043 pass for Utils)
- [X] T047 [P] [US3] Rewrite `modules/AttackSpells.py` as `AttackSpellsFeature` (`key="attack_spells"`, `requires={BATTLE_LIST}`) using `battle_entries` and the `attack_spells` settings (makes T043 pass for spells)
- [X] T048 [US3] Rewrite `modules/CaveBot.py` as `AttackFeature` (`key="attack"`, `requires={BATTLE_LIST}`), `LootFeature` (`key="loot"`, `requires={CHAT, GAME_VIEW}`; Shift released in `finally`; tile offsets replace `loot_points_list`) and `WalkFeature` (`key="walk"`, `requires={MINIMAP, BATTLE_LIST}`; mark searched only inside the minimap; arrival via `is_arrived`; replace the bare `except:` with handling of `find_mark` returning None that presses `refresh_map` once per missing mark and logs it). Walking waits while the battle list shows monsters, as today (makes T042 pass)
- [X] T049 [P] [US3] Update `Waypoints.py`: `list_routes()` returns each file in `data/` with `valid` and a list of missing mark paths; `select_json()` keeps its current return value (makes T044 pass)
- [X] T050 [US3] Register all eight features in `App.py` in contract order (healing, mana_refill, eating, attack_spells, chase, attack, loot, walk); delete `config/Config.py`, `config/PixelConfig.py`, `config/KeysConfig.py`, `config/ImageProcessingConfig.py` and `helpers/Helpers.py`, and confirm with a search that nothing imports them
- [X] T051 [US3] Finish the Run tab in `ui/MainWindow.py` per contracts/ui-controls.md: a Start/Stop button per feature (disabled with no client selected), unchecking Enabled stops a running feature, route combo under the Walk row from `list_routes()` showing invalid routes as `<name> (invalid)` and not selectable, the active route shown, route saved to `cavebot.route`
- [X] T052 [US3] Build the Settings tab in `ui/MainWindow.py`: grouped inputs for every field in contracts/settings-schema.md except `version` and `features`; invalid values shown in red and blocking Save; Save validates, writes through `SettingsStore` on the UI thread and calls `apply_settings`; Revert discards edits; a warning line when `load()` returned warnings (FR-023)

**Checkpoint**: Tests T041–T044 pass; quickstart steps 9–12 and 14 behave as described; US1 and
US2 still work

---

## Phase 6: User Story 4 - See what the bot is doing (Priority: P3)

**Goal**: Show each feature's state and a log of recent actions and problems.

**Independent Test**: Run Healing and Walk, hide a route mark, and confirm the Log tab shows the
failed search and the map refresh (quickstart step 13).

### Tests for User Story 4 ⚠️ write first, confirm they fail

- [X] T053 [P] [US4] Extend `tests/test_Supervisor.py` (part 3): every pause, resume, start, stop, detection change and `ctx.log` call adds one `ActivityLogEntry` with the right `source` (feature key, `detection`, `settings` or `supervisor`) and `level`; the buffer keeps only the newest 500 entries

### Implementation for User Story 4

- [X] T054 [US4] Audit `core/Supervisor.py`, `core/LayoutMonitor.py` and `config/Settings.py` callers so every event in FR-011 is logged (detection failure, pause, resume, recovery action, settings warning) (makes T053 pass)
- [X] T055 [US4] Build the Log tab in `ui/MainWindow.py` per contracts/ui-controls.md: newest 100 entries (time, source, level, message), warnings and errors coloured, filter combo (All / each feature / detection), Clear button that clears only the view

**Checkpoint**: Test T053 passes; quickstart step 13 behaves as described

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Documentation, audits, and end-to-end validation

- [X] T056 [P] Update `CLAUDE.md` for the new architecture: commands (`pip install -r requirements.txt`, `helpers/CaptureClient.py`), packages `core/`, `detection/`, `config/Settings.py`, `config/DetectionConfig.py`, `ui/`, the feature contract, the bot thread / UI thread split, and the removal of the 800x600 assumption and `PixelConfig`-style properties
- [ ] T057 [P] Update `README.md`: any window size and display scaling, official client only, the UI tabs, and setup steps
- [X] T058 [P] Write `tests/test_Principles.py`: parse every file in `modules/` with `ast` and fail on numeric tuple literals of length 2 or 4 used as coordinates, on bare `except:`, and on `time.sleep` (Principles I, II, VI)
- [X] T059 Run `python -m unittest discover -v -s ./tests -p "test_*.py"` and fix failures until everything passes
- [ ] T060 MANUAL: run all of quickstart.md section 3 (steps 1–15) at 800x600 and maximized 1920x1080, plus steps 2, 4 and 12 at 125% display scaling, and record results in `specs/001-auto-detect-layout-ui/checklists/validation.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: no dependencies
- **Foundational (Phase 2)**: depends on Setup; blocks every user story
- **US1 (Phase 3)**: depends on Foundational. T019–T021 are MANUAL and need T018 (capture helper)
- **US2 (Phase 4)**: depends on US1 (it needs real Layouts to pause and resume against)
- **US3 (Phase 5)**: depends on US1 (detection) and US2 (the ready gate every feature uses)
- **US4 (Phase 6)**: depends on Foundational for the log; its manual test needs US3's Walk feature
- **Polish (Phase 7)**: depends on all stories

### User Story Dependencies

```text
Setup ─▶ Foundational ─▶ US1 ─▶ US2 ─▶ US3 ─▶ Polish
                    └──────────────▶ US4 (log tab can start after Foundational;
                                          its acceptance test needs US3)
```

The stories are not independent of each other: every feature needs detection (US1), and every
feature acts only through the ready gate (US2). Each story still ends at a working, testable
increment.

### Within Each User Story

- Fixtures (US1 only), then tests (confirm they fail), then readers/detection, then core
  services, then features, then UI
- `detection/` before `core/` before `modules/` before `ui/`

### Parallel Opportunities

- Phase 1: T002, T003
- Phase 2: tests T004–T007 together; then T008–T013 together; T018 alongside T014–T017
- US1: T023 and T024 together; T025 and T030 alongside the detector work (T026–T028)
- US2: T032–T035 together; T036 alongside T037
- US3: T041–T044 together; T046, T047 and T049 together after T045
- US4: T053 can be written while US3 is in progress
- Polish: T056, T057, T058 together

---

## Parallel Example: User Story 1

```text
# After the MANUAL fixtures (T019–T021) and T022:
Task: "Write tests/test_LayoutDetector.py per contracts/layout-detector.md"   (T023)
Task: "Write tests/test_Templates.py"                                         (T024)

# Then:
Task: "Implement detection/Templates.py"                                      (T025)
Task: "Implement ui/DetectionPreview.py"                                      (T030)
```

## Parallel Example: User Story 3

```text
Task: "Extend tests/test_Readers.py (part 2)"                                 (T041)
Task: "Rewrite tests/test_CaveBot.py with a fake FeatureContext"              (T042)
Task: "Write tests/test_Utils.py and tests/test_AttackSpells.py"              (T043)
Task: "Write tests/test_Waypoints.py"                                         (T044)

# After T045:
Task: "Rewrite modules/Utils.py"                                              (T046)
Task: "Rewrite modules/AttackSpells.py"                                       (T047)
Task: "Update Waypoints.py list_routes()"                                     (T049)
```

---

## Implementation Strategy

### MVP First (User Story 1)

1. Phase 1 and Phase 2
2. MANUAL fixture capture (T019–T021); this is the step most likely to block progress, so do
   it as soon as T018 exists
3. Rest of Phase 3
4. **STOP and VALIDATE**: quickstart steps 1–3 at two window sizes

### Incremental Delivery

1. US1 → detection visible in the UI (MVP)
2. US2 → Healing and Mana refill working at any size, with safe pausing. This is the first
   release that replaces the old bot for healing.
3. US3 → all eight features and full settings, replacing the old bot completely
4. US4 → activity log
5. Polish → docs, principle audit, full manual validation

---

## Notes

- **Blocker found during /speckit-implement (2026-10-22)**: the official client window has display
  affinity `WDA_MONITOR` (`GetWindowDisplayAffinity` returns `0x1`). Windows then returns black
  for that window to every capture API (`mss`, `ImageGrab`, Print Screen, `PrintWindow`, Windows
  Graphics Capture); a capture of the visible, focused client was all zeros. T019–T022 and T060
  cannot be done against the official client, and the bot cannot read it. Circumventing the
  protection is out of scope. Re-scoping (for example to a client that allows capture) needs a
  spec change via `/speckit-specify` or `/speckit-clarify`.
- The scope clarification (all eight features now vs. healing/mana/eating first) was not
  answered. All eight are included, in US3. To ship sooner, stop after US2 and move T045–T051
  into a follow-up feature.
- Plan Complexity Tracking suggests a PATCH amendment to constitution Principle I ("gathered by
  `asyncio.gather`" → per-feature tasks). Run `/speckit-constitution` for it separately; it is
  not a task here.
- Commit after each task or logical group, using the `(type): summary` convention.
- Every feature loop path must `await` (Principle I); T058 checks for `time.sleep`.
