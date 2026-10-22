# MMORPG-Bot Constitution

## Core Principles

### I. Cooperative Concurrency

Features run as `async` loops gathered by `asyncio.gather` on a single thread.

- Every feature MUST be exposed as one `async` loop method on its module class.
- Every branch of every loop iteration MUST reach an `await asyncio.sleep(...)`. A path that
  skips the `await` starves every other feature and is a defect.
- Blocking calls (`time.sleep`, `pyautogui`, screen capture) MUST stay short; long waits MUST use
  `await asyncio.sleep` instead of `time.sleep`.
- Every loop MUST be stoppable: it MUST check a cancellation signal each iteration so the UI can
  stop it without killing the process.

Rationale: concurrency is cooperative, so one non-yielding loop freezes healing, looting, and
walking at once.

### II. Runtime-Detected Layout

The bot MUST work with the Tibia client at any window size, resolution, and position, without
manual calibration.

- The bot MUST locate the Tibia client window automatically (by window title or process) and
  derive all capture regions from that window's current bounds.
- The bot MUST detect the client's UI components on screen (at minimum: health bar, mana bar,
  minimap, game view and character position, chat/server log, battle list, and status icons
  such as hunger) using resolution- and scale-tolerant detection, not fixed coordinates.
- Every coordinate used for capturing, pixel checks, or clicks MUST be computed from detected
  component geometry. Absolute screen coordinates and resolution-specific constants are
  prohibited.
- The bot MUST re-run detection when the window moves, resizes, or changes layout, and when a
  detected component stops matching.
- If the window or a component a feature needs cannot be detected, that feature MUST pause and
  report the failure; it MUST NOT act on stale or guessed coordinates.

Rationale: hard-coded 800x600 coordinates break on any other setup; detecting the layout makes
the bot portable and stops it from clicking blindly.

### III. Centralized Configuration

- Hotkeys, detection references (template images, colour ranges, match thresholds), and timing
  values MUST live in one configuration layer and be read through typed accessors, not
  scattered literals in feature code.
- Positions inside a component (for example, the pixel that means "HP below 70%") MUST be
  expressed relative to that component's detected bounds, as fractions or component-relative
  offsets, never as screen pixels.
- Every accessor MUST map to an existing key; an unknown key MUST raise an error, not return
  `None` silently.
- User-editable settings MUST persist to a file and survive restarts.

Rationale: one source of truth keeps tuning in one place, and relative values keep it valid at
every resolution.

### IV. Screen-Independent Testability

Decision logic MUST be separable from screen I/O.

- Detection and image-analysis logic MUST live in functions that accept an image and return a
  result, so they run on fixture screenshots.
- Constructors MUST NOT capture the screen, press keys, or move the mouse; tests instantiate
  modules at import time.
- New or changed detection or analysis logic MUST ship with `unittest` tests using fixtures in
  `tests/testdata/`, covering at least two different client resolutions or window sizes.

Rationale: the game is not available in tests, and detection that is only tested at one size
will not work at another.

### V. UI-Managed Operation

Everything the bot does MUST be manageable from its UI; no normal use requires editing code or
config files by hand.

- The UI MUST start and stop the bot and each feature individually, at any time.
- The UI MUST show detection status: whether the Tibia window was found and which components
  were detected, with a way to view the detected regions (for example, an overlay or preview).
- The UI MUST let the user edit hotkeys, thresholds (heal/mana percentages, food interval, and
  similar), and waypoint lists, and MUST save those settings (Principle III).
- The UI MUST surface paused features and detection failures (Principle II) to the user.
- A feature MUST NOT act while it is disabled in the UI.

Rationale: auto-detection removes calibration; the UI removes the remaining need to touch code.

### VI. Simplicity and Explicit Recovery

- Prefer the simplest detection or pixel check that works reliably; new dependencies MUST be
  justified in the plan.
- Error handling MUST catch the specific failure it recovers from and perform a defined recovery
  action (for example, re-detect the layout); new bare `except:` blocks are prohibited.
- Recovery actions and detection failures MUST be logged so they can be shown in the UI.

Rationale: an automation loop that hides errors keeps clicking blindly in the game.

## Technical Constraints

- Platform: Windows, Python 3. Current runtime dependencies are `dearpygui` (pre-1.0 API),
  `pyautogui`, `Pillow`, and `numpy`. Changing the UI framework or adding a detection library
  (for example, OpenCV) is allowed when the plan justifies it.
- Window discovery MUST use Windows APIs (or a library wrapping them) rather than assuming the
  client fills the screen.
- All commands run from the repository root; paths such as `./data`, `images/`, and
  `tests/testdata/` are relative to it.
- Waypoint files in `data/*.json` MUST keep the form `{"waypoints": [<image path>, ...]}`, with
  each path pointing to an icon in `images/marks/`, unless a plan defines a migration.

## Development Workflow

- Before merging, the full suite MUST pass:
  `python -m unittest discover -v -s ./tests -p "test_*.py"`.
- Changes to loop control flow MUST be reviewed against Principle I (every branch awaits, every
  loop stoppable).
- Changes to detection MUST be reviewed against Principle II and include fixtures at two or more
  resolutions (Principle IV).
- New user-facing settings MUST be added to the UI in the same change (Principle V).
- Commit messages use the `(type): summary` convention already in history, e.g. `(feat):`,
  `(fix):`, `(tests):`, `(doc):`.
- `CLAUDE.md` holds runtime development guidance and MUST be updated when architecture or
  commands change.

## Governance

This constitution supersedes other project practices. Where `CLAUDE.md` or a plan conflicts with
it, the constitution wins until amended.

- Amendments are made by editing this file through `/speckit-constitution`, with a Sync Impact
  Report describing the change.
- Versioning follows semantic versioning: MAJOR for removing or redefining a principle, MINOR for
  adding a principle or section or materially expanding guidance, PATCH for clarifications.
- Every spec, plan, and review MUST check compliance with the Core Principles; any deviation MUST
  be recorded with its justification in the plan's complexity tracking.

**Version**: 2.0.0 | **Ratified**: 2026-10-22 | **Last Amended**: 2026-10-22
