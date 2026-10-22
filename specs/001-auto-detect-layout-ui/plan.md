# Implementation Plan: Auto-Detected Layout and Management UI

**Branch**: `001-auto-detect-layout-ui` | **Date**: 2026-10-22 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/001-auto-detect-layout-ui/spec.md`

## Summary

Replace the bot's fixed 800x600 coordinates with a layout that is detected at runtime from the
official Tibia client window, and replace the start-only control window with a management UI.

Approach (see [research.md](./research.md)):

- Find the client window through the Win32 API (title + process name), in a DPI-aware process, and
  capture only that window's client area.
- A pure `LayoutDetector` takes a capture of the client and returns a `Layout`: one region per
  component, found by multi-scale template matching on small anchor images (heart icon, mana
  icon, "Battle List" title, minimap buttons, chat tabs, combat-mode buttons) plus geometry
  measured relative to each anchor. The game view is found as the largest 15:11 tile area.
- Pure readers turn a component capture into a value: bar fill percent, battle-list entries,
  chase on/off, hunger present, loot message present, waypoint mark position on the minimap.
- A `LayoutMonitor` loop watches the window rectangle and component health and re-detects when
  either changes. A `Supervisor` runs each feature as its own asyncio task, pauses a feature
  while any component it needs is missing (or the client is not in the foreground), and
  cancels tasks on Stop.
- The UI runs Dear PyGui 2.x on the main thread; the bot's asyncio loop runs on one worker
  thread. The two talk only through thread-safe calls on the Supervisor and a read-only status
  snapshot.
- Settings (hotkeys, thresholds, timings, route, chosen client) are a typed dataclass saved as
  JSON in `settings.json` and applied live.

Scope note: the clarification on scope (all eight features vs. healing/mana/eating first) was
not answered, so this plan keeps FR-025 as written: all eight features move to detected
positions. Tasks will still order healing, mana refill and eating first so they can ship early.

## Technical Context

**Language/Version**: Python 3.13 (the interpreter installed on the target machine)

**Primary Dependencies**: `dearpygui` 2.x (UI), `opencv-python` (template matching, contour
search), `numpy` 2.x, `mss` (screen capture), `pywin32` (window discovery, foreground check),
`psutil` (process name of a window), `pyautogui` (keyboard/mouse input), `Pillow` (fixture
loading). Pinned in a new `requirements.txt`.

**Storage**: `settings.json` at the repository root (git-ignored); waypoint routes stay in
`data/*.json`; detection templates are PNG files in `images/ui/`.

**Testing**: `unittest` (`IsolatedAsyncioTestCase` for async parts), run with
`python -m unittest discover -v -s ./tests -p "test_*.py"`. Detection and readers are tested on
full-client screenshots in `tests/testdata/` at 800x600 and 1920x1080 (Principle IV).

**Target Platform**: Windows 10/11 desktop, official Tibia client, any window size, display
scaling 100–200%.

**Project Type**: Desktop application (single Python project).

**Performance Goals**: full layout detection under 1 s on a 1920x1080 client (SC: found within
5 s); window change noticed within 0.5 s and re-detection done within 3 s (SC-003); each
feature loop pass under 100 ms of blocking work; Stop takes effect within 1 s (SC-005); UI stays
at interactive frame rate while the bot runs.

**Constraints**: features must not send input while their components are missing or the client
is not the foreground window (FR-009); no absolute screen coordinates in feature code
(Principle II); the bot runs on the same machine as the client.

**Scale/Scope**: one client at a time; 8 features; about 8 detected component types; about 20
template images.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Gate | Pre-research | Post-design |
|-----------|------|--------------|-------------|
| I. Cooperative Concurrency | Every loop branch awaits; every loop stoppable | Pass: features run as asyncio tasks on one worker thread | Pass: feature contract requires an `await` per pass; Supervisor cancels tasks and checks a stop event ([feature-interface](./contracts/feature-interface.md)) |
| II. Runtime-Detected Layout | Window and components detected; no absolute coordinates; re-detect on change; pause on missing | Pass | Pass: `LayoutDetector` + `LayoutMonitor`; features receive positions only from `Layout` ([layout-detector](./contracts/layout-detector.md)) |
| III. Centralized Configuration | One config layer, typed accessors, relative values, unknown key raises, persisted | Pass | Pass: `Settings` dataclass + `DetectionConfig`; thresholds in percent, offsets in tile or component units ([settings-schema](./contracts/settings-schema.md)) |
| IV. Screen-Independent Testability | Pure detection/readers; no screen I/O in constructors; fixtures at 2+ sizes | Pass | Pass: detector and readers take `numpy` images; fixtures at 800x600 and 1920x1080 |
| V. UI-Managed Operation | Start/stop all and each feature; detection status and preview; edit settings; show pauses | Pass | Pass: [ui-controls](./contracts/ui-controls.md) |
| VI. Simplicity and Explicit Recovery | Justified dependencies; no bare `except:`; recoveries logged | Pass with justification (new dependencies listed in research.md) | Pass: the CaveBot bare `except` becomes a specific "mark not found" recovery that is logged |
| Technical Constraints | Windows APIs for window discovery; UI framework change justified | Pass: Dear PyGui pre-1.0 has no Python 3.13 build; moving to 2.x is justified in research.md | Pass |

No unjustified violations. One wording deviation is recorded under Complexity Tracking.

## Project Structure

### Documentation (this feature)

```text
specs/001-auto-detect-layout-ui/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── feature-interface.md
│   ├── layout-detector.md
│   ├── settings-schema.md
│   └── ui-controls.md
└── tasks.md             # Phase 2 output (/speckit-tasks, not created here)
```

### Source Code (repository root)

New files follow the existing convention: lowercase package directories, one class per
CapitalCase module.

```text
App.py                         # entry point: sets DPI awareness, starts ui.MainWindow
requirements.txt               # new: pinned dependencies
settings.json                  # new, git-ignored: saved user settings

core/
├── __init__.py
├── ClientWindow.py            # find official client windows (Win32), rect, foreground, state
├── ScreenCapture.py           # capture client area / sub-regions to numpy arrays (mss)
├── GameInput.py               # key presses and clicks; refuses input when client not foreground
├── ActivityLog.py             # thread-safe ring buffer of log entries
├── LayoutMonitor.py           # async loop: watch window, re-detect, publish Layout
└── Supervisor.py              # owns the event loop thread, feature tasks, pause/resume, stop

detection/
├── __init__.py
├── Components.py              # ComponentType, Region, DetectedComponent, Layout
├── Templates.py               # load images/ui/*.png once, build scaled variants
├── LayoutDetector.py          # pure: detect_layout(image, templates, config) -> Layout
└── Readers.py                 # pure: bar_percent, battle_entries, chase_on, hunger_present,
                               #       loot_message_present, find_mark_on_minimap

config/
├── __init__.py
├── Settings.py                # Settings dataclasses + SettingsStore (load/save/defaults)
└── DetectionConfig.py         # anchor template names, geometry, colour ranges, thresholds
                               # (Config.py, PixelConfig.py, KeysConfig.py,
                               #  ImageProcessingConfig.py are removed)

modules/                       # existing features, rewritten against the Feature contract
├── Healing.py                 # HealingFeature, ManaRefillFeature
├── Utils.py                   # EatingFeature, ChaseFeature
├── AttackSpells.py            # AttackSpellsFeature
└── CaveBot.py                 # AttackFeature, LootFeature, WalkFeature

ui/
├── __init__.py
├── MainWindow.py              # control window: tabs Run / Detection / Settings / Log
└── DetectionPreview.py        # renders the client capture with region outlines

helpers/
├── Helpers.py                 # removed once GameInput/ScreenCapture replace it
├── QuickSS.py                 # kept for cropping templates
└── CaptureClient.py           # new: save a full client capture for fixtures/templates

images/
├── marks/                     # unchanged waypoint marks
└── ui/                        # new: anchor templates cropped from the official client

tests/
├── test_CaveBot.py            # updated to new LootFeature reader
├── test_ClientWindow.py       # window filtering on fake window lists
├── test_LayoutDetector.py     # 800x600 and 1920x1080 fixtures
├── test_Readers.py            # bars, battle list, chase, hunger, loot, marks
├── test_Settings.py           # defaults, round-trip, damaged file
├── test_Supervisor.py         # pause/resume/stop with fake features and layouts
└── testdata/
    ├── client_800x600.png     # new full-client captures
    ├── client_1920x1080.png
    ├── client_1920x1080_no_battle_list.png
    └── (existing crops kept for the loot tests)
```

**Structure Decision**: single desktop project. New `core/`, `detection/` and `ui/` packages sit
next to the existing `modules/`, `config/` and `helpers/`. `detection/` contains only pure
functions (no screen or input access) so it can be tested on fixtures; `core/` holds everything
that touches Windows, the screen or the keyboard.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Principle I says features are "gathered by `asyncio.gather`"; this plan runs each feature as its own `asyncio.Task` under a Supervisor | FR-012 needs each feature started and stopped on its own while others keep running | One `gather` call can only be cancelled as a whole. The intent of Principle I (one thread, cooperative, every branch awaits) is kept. Suggest a PATCH amendment to reword the sentence. |
| UI and bot on two threads (UI main thread, one asyncio worker thread) | FR-013: the UI must stay responsive; Dear PyGui's render loop blocks its thread | Running the asyncio loop inside the render loop ties feature timing to frame rate and lets a slow capture freeze the UI. Features still share one thread. |
