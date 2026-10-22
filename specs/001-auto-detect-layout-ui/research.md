# Research: Auto-Detected Layout and Management UI

**Feature**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md) | **Date**: 2026-10-22

Facts about the official client's pixel geometry (exact anchor offsets, bar colours, panel
widths) cannot be confirmed without the client. Where a decision depends on them, it says
**Measure**: the value is taken from the full-client fixtures during implementation and stored in
`config/DetectionConfig.py`, never in feature code.

## R1. Python version and UI framework

- **Decision**: Target Python 3.13 and move the UI to Dear PyGui 2.x.
- **Rationale**: The machine has Python 3.13.0. The pre-1.0 Dear PyGui API used by `App.py`
  (`setup_viewport`, `add_spacing`, `start_dearpygui`) has no Python 3.13 build, so the current
  UI cannot be installed as-is. Dear PyGui 2.x keeps the same immediate-mode model and
  always-on-top viewport, has tabs, tables, textures (for the detection preview) and drawlists
  (for region outlines), and needs no extra runtime. The constitution allows a framework change
  when the plan justifies it.
- **Alternatives considered**: Tkinter (built in, but no GPU texture for a live preview and
  more code for the same window); PySide6 (capable, but a large dependency and licence surface
  for a small control window); pinning an old Python to keep Dear PyGui 0.x (blocks every other
  dependency upgrade).

## R2. Finding the official client window

- **Decision**: Enumerate top-level windows with `win32gui.EnumWindows`. Keep windows that are
  visible, have a title starting with `Tibia`, and whose process executable (via
  `win32process.GetWindowThreadProcessId` + `psutil.Process(pid).exe()`) is the official
  client's `client.exe` inside a folder whose path contains `Tibia`. Measure: confirm the
  executable name and title format on the target install; store both in `DetectionConfig`.
  Use the client area (`GetClientRect` + `ClientToScreen`), not the outer frame.
- **Rationale**: The title alone also matches browser tabs and OpenTibia clients, which FR-001
  says must not be offered. Process name plus title is cheap and has no false positives in
  practice. Several matches are listed in the UI (FR-002) and keyed by window handle.
- **Alternatives considered**: `pygetwindow` (title only, cannot check the process);
  searching the screen for the client by image (slow, and cannot tell two clients apart).

## R3. Display scaling and coordinates

- **Decision**: Call `SetProcessDpiAwareness(2)` (per-monitor DPI aware) through `ctypes` as the
  first line of `App.py`, before any window, capture or input library is imported. All
  coordinates are then physical pixels on the virtual desktop, which is what window rects,
  `mss` captures and `pyautogui` clicks all use.
- **Rationale**: Without it, Windows reports scaled coordinates to the bot while captures are in
  physical pixels, so clicks land in the wrong place at 125–200% scaling (spec edge case).
- **Alternatives considered**: converting coordinates by the monitor's scale factor in code
  (error-prone across mixed-DPI monitors).

## R4. Screen capture

- **Decision**: Use `mss` to grab the client rectangle (or a sub-region of it) into a `numpy`
  BGRA array, converted to BGR for OpenCV. One `mss` instance lives on the bot thread.
- **Rationale**: `mss` is several times faster than `ImageGrab.grab` per call, works on
  secondary monitors and negative coordinates, and returns arrays without a PIL round trip. Each
  feature pass grabs only its component's region.
- **Alternatives considered**: `PIL.ImageGrab` (works, but slower and needs `all_screens=True`
  for other monitors); Windows Graphics Capture / `PrintWindow` on the client window (can capture
  an obscured window, but hardware-accelerated clients often return black frames through
  `PrintWindow`, and WGC adds a native dependency. A possible later improvement for the
  "client covered by another window" edge case.)

## R5. Component detection method

- **Decision**: Anchor-based, multi-scale template matching with OpenCV.
  1. For each component, a small anchor template cropped from the official client is matched
     (`cv2.matchTemplate`, `TM_CCOEFF_NORMED`) over the client capture at scales
     `1.0, 1.25, 1.5, 1.75, 2.0`. The best scale found for the first anchor is reused for the
     rest, so a full pass costs about 1 scale search plus 7 single-scale searches.
  2. A match counts as found when the score is at least `match_threshold` (default `0.85`,
     tunable in `DetectionConfig`).
  3. The component region is the anchor box plus an offset and size measured relative to the
     anchor, multiplied by the found scale. Measure: offsets and sizes from the fixtures.

  Anchors:

  | Component | Anchor | Region derived from anchor |
  |-----------|--------|----------------------------|
  | Health bar | heart icon | bar to the right of the icon, same row |
  | Mana bar | mana icon | bar to the right of the icon, same row |
  | Battle list | "Battle List" window title | list body below the title, panel width |
  | Minimap | minimap control buttons (zoom/floor) | minimap square to the left of the buttons |
  | Combat controls (chase) | chase-mode button, on and off variants | the button itself; which variant matched gives on/off |
  | Status icons (hunger) | status/conditions strip anchor | the strip; hunger is a second template searched inside it |
  | Chat / server log | chat tab bar ("Server Log" tab) | message area above the tab bar |
  | Game view | none (see R6) | — |

- **Rationale**: In the official client the side panels and icons are drawn at a fixed pixel
  size; only the game view stretches with the window. Anchors therefore look the same at every
  window size, and multi-scale search covers Windows display scaling. Template matching on
  small anchors is fast (well under 1 s for a 1920x1080 capture), deterministic, and testable
  on fixtures. Measure: confirm at implementation time that panel icons do not change size with
  window size; if the client has a UI-scale option, its values join the scale list.
- **Alternatives considered**: feature matching (ORB/SIFT; slower and unstable on flat UI
  graphics); a trained object detector (needs labelled data and a model runtime, against
  Principle VI); colour-only segmentation (breaks when panels are rearranged or themed).

## R6. Game view, tile size, and character position

- **Decision**: Find the game view as the largest axis-aligned rectangle in the client capture
  whose aspect ratio is within 3% of 15:11 (the client shows 15x11 tiles), using an edge map
  (`cv2.Canny`) and `cv2.findContours`. Tile size = game view width / 15; the character stands
  in the centre tile (column 7, row 5, counting from 0). Loot positions are the 8 tiles around
  the character plus the centre tile, expressed as tile offsets `(-1..1, -1..1)` and converted
  to screen points at use time.
- **Rationale**: The game view stretches with the window, so no fixed template exists, but its
  tile grid is fixed. Using tile offsets replaces today's absolute `loot_points_list`.
- **Alternatives considered**: deriving the game view from panel positions (breaks when the
  user moves panels); asking the user to draw the game view once (violates "no calibration").
  Measure: if the client draws black letterbox bars, the contour search also has to ignore the
  bars; covered by the 1920x1080 fixture.

## R7. Reading values from components

- **Decision**: Pure functions in `detection/Readers.py`, each taking the component's image:
  - `bar_percent(image)`: scan the middle row of the bar; a pixel counts as filled when its HSV
    saturation and value are above thresholds (the empty part of the bar is dark and grey).
    Percent = filled run length / bar width x 100. This gives real percentages for FR-017
    instead of today's single-pixel checks.
  - `battle_entries(image)`: number of monster rows (row height measured relative to scale) and
    whether any row has the red "targeted" frame, replacing `battle_list`,
    `battle_list_two_monsters`, `battle_list_three_monsters` and `monster_red`.
  - `chase_on(layout)`: which chase-button variant matched.
  - `hunger_present(image)`: hunger template found in the status strip.
  - `loot_message_present(image)`: any pixel equal to the loot colour (today `[240, 180, 0]`;
    Measure: confirm on the official client).
  - `find_mark(minimap_image, mark_template, scale)`: best match of a waypoint mark inside the
    minimap region only, returning a point relative to the minimap.
- **Rationale**: Each reader is a small pure function with one fixture test; features compose
  them.
- **Alternatives considered**: OCR of HP/mana numbers (needs an OCR engine; the bars are
  enough).

## R8. Waypoint walking on any minimap size

- **Decision**: Search for the route's mark only inside the detected minimap, at the detected
  scale. "Reached" means the mark's centre is within `arrival_radius` (default 6% of the minimap
  width) of the minimap centre, where the character always is. Click the mark at its detected
  screen position. Existing `data/*.json` files stay valid (FR-024).
- **Rationale**: Replaces the absolute `between` box and the full-screen
  `locateCenterOnScreen`, which was slow and could match marks elsewhere on screen.
- **Alternatives considered**: whole-screen search (today's behaviour, too slow and ambiguous).

## R9. Concurrency, start/stop and pausing

- **Decision**:
  - The UI owns the main thread (Dear PyGui render loop). `Supervisor` starts one daemon thread
    running one asyncio event loop. Everything that captures, reads or sends input runs on that
    loop.
  - The UI calls only thread-safe Supervisor methods (`start_feature`, `stop_feature`,
    `start_all`, `stop_all`, `apply_settings`), which use `loop.call_soon_threadsafe`. The UI
    reads a `StatusSnapshot` (immutable, replaced atomically) each frame.
  - Each feature is one `asyncio.Task`. Stop = `task.cancel()`; features treat
    `CancelledError` as normal exit (they release held keys such as Shift in `finally`).
  - Before each pass, the Supervisor-provided context checks: client found, client in the
    foreground, every required component found. If not, the feature waits on a "layout changed"
    `asyncio.Event` with a 0.5 s timeout instead of acting, and its state becomes
    `paused(reason)` (FR-008 to FR-010).
- **Rationale**: Per-feature tasks are the only way to stop one feature while others keep
  running (FR-012). One worker thread keeps Principle I's cooperative model, and the UI thread
  can never be blocked by a capture (FR-013).
- **Alternatives considered**: a single `asyncio.gather` (cannot stop one feature); a thread
  per feature (races on input and capture, against Principle I); running the asyncio loop
  inside the render loop (frame-rate-bound timing).

## R10. Re-detection triggers

- **Decision**: `LayoutMonitor` polls the client rectangle and minimized/foreground state every
  0.25 s (cheap Win32 calls). It re-runs full detection when the rect changes (after a 0.3 s
  settle delay so a drag does not trigger many passes), when the window is restored, and when a
  feature reports that a component stopped matching (for example, an anchor re-check fails or a
  bar reads outside 0–100). A light re-check of each anchor at its known position runs every
  2 s. Detection takes under 1 s, so re-detection finishes within 3 s (SC-003).
- **Rationale**: Event hooks (`SetWinEventHook`) would need a message pump on the bot thread;
  polling is simpler and fast enough.
- **Alternatives considered**: `SetWinEventHook` for move/size events (more complex, same
  result).

## R11. Input safety

- **Decision**: `GameInput` wraps `pyautogui` and refuses to send anything unless the selected
  client window is the foreground window (`win32gui.GetForegroundWindow`). Clicks take points
  produced from the current `Layout` only. `pyautogui.FAILSAFE` stays on. Each refusal is a
  pause with reason "client not focused", not an error.
- **Rationale**: `pyautogui` sends keys to whatever window has focus. Without this check,
  pressing Stop in the UI and then any feature pass would type hotkeys into the UI or another
  app (FR-009). It also covers the "control window covers the client" edge case.
- **Alternatives considered**: sending input with `PostMessage` to the client window
  (works in the background, but game clients often ignore synthetic messages; keep for later).

## R12. Settings storage

- **Decision**: `config/Settings.py` defines dataclasses (`Hotkeys`, `HealingSettings`,
  `ManaSettings`, `EatingSettings`, `AttackSpellSettings`, `CaveBotSettings`, `Settings`)
  with defaults equal to today's values (`f1` attack, `f8`/`f4` heal, `f7` mana, `f5` food,
  and so on). `SettingsStore` saves them as JSON to `./settings.json` (git-ignored), writing to a
  temp file and renaming so a crash never leaves a half-written file. On a damaged or invalid
  file it renames it to `settings.json.bad`, loads defaults, and logs a warning shown in the UI
  (FR-023). Unknown keys are dropped with a warning; accessing a missing attribute raises
  (Principle III). Detection constants live in `config/DetectionConfig.py`, not in user settings.
- **Rationale**: Standard library only; human-readable; fits the existing JSON route files.
- **Alternatives considered**: INI (`configparser`; no nesting or lists); SQLite (overkill);
  keeping module-level dicts (cannot be saved from the UI).

## R13. Fixtures and templates

- **Decision**: Add `helpers/CaptureClient.py`, which saves a full client-area capture of the
  selected client to `tests/testdata/`. Needed before detection can be built and tested:
  - `client_800x600.png`, `client_1920x1080.png` (default layout, battle list open, a monster
    in the battle list, minimap with a mark);
  - `client_1920x1080_no_battle_list.png` (missing-component case);
  - one capture at 125% display scaling (`client_1920x1080_125.png`);
  - anchor templates cropped from these captures into `images/ui/`.
- **Rationale**: Principle IV requires fixtures at two or more sizes, and anchor templates must
  come from the real client. This is a manual step a person must do with the game running; tasks
  mark it so.
- **Alternatives considered**: synthetic fixtures (would not prove anything about the real
  client).

## R14. Dependencies

| Package | Use | Justification (Principle VI) |
|---------|-----|------------------------------|
| `dearpygui` 2.x | UI | Existing choice, upgraded for Python 3.13 (R1) |
| `opencv-python` | template matching, contours | Core of resolution-independent detection (R5, R6); `pyautogui`'s own matcher is single-scale and slow |
| `numpy` 2.x | image arrays | Existing |
| `mss` | screen capture | Speed and multi-monitor support (R4) |
| `pywin32` | window discovery, foreground check | Required by the constitution's Technical Constraints (R2) |
| `psutil` | window → process executable | Filters out non-official clients (R2) |
| `pyautogui` | input | Existing |
| `Pillow` | load fixture PNGs, preview textures | Existing |

Versions are pinned in `requirements.txt` at implementation time to the newest releases with
Python 3.13 wheels.

## Open items

- None blocking. The **Measure** values above are filled from fixtures during implementation.
- Scope question from `/speckit-clarify` (all eight features now vs. healing/mana/eating first)
  is unanswered; the plan keeps all eight (FR-025).
