# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

Pixel-based MMORPG bot (Windows, Python 3.13). It finds the game client window, detects the client's UI components (health/mana bars, battle list, minimap, chat, combat controls, status icons, game view) on a capture of that window at any size, then drives the client with `pyautogui` key presses and mouse clicks. Features: healing, mana refill, eating, attack spells, auto chase, monster attacking, looting, and waypoint walking via minimap clicks. Governing rules are in `.specify/memory/constitution.md`; the current feature's design is in `specs/001-auto-detect-layout-ui/`.

**Known blocker**: the official Tibia client sets display affinity `WDA_MONITOR` on its window, so every screen-capture API returns black for it. Detection cannot work against that client; see `specs/001-auto-detect-layout-ui/tasks.md` notes.

## Commands

All commands run from the repo root, because paths such as `./data`, `./settings.json`, `images/...` and `tests/testdata/...` are relative to the working directory. Dependencies are pinned in `requirements.txt` and installed in `.venv`.

- Install: `python -m venv .venv` then `.venv\Scripts\python -m pip install -r requirements.txt`
- Run the app (Dear PyGui 2.x control window): `.venv\Scripts\python App.py`
- Run all tests (matches `.vscode/settings.json`): `.venv\Scripts\python -m unittest discover -v -s ./tests -p "test_*.py"`
- Run a single test: `.venv\Scripts\python -m unittest tests.test_CaveBot.TestWalk.test_wraps_to_first_mark`
- Save a capture of the client for fixtures/templates: `.venv\Scripts\python helpers/CaptureClient.py tests/testdata/<name>.png [--title <part of title>]`

## Architecture

**Threads**: `App.py` sets per-monitor DPI awareness first (`core/Dpi.py`, before `pyautogui`/`mss`/`dearpygui` are imported), loads settings, registers the features with a `Supervisor`, and runs the UI. The UI (`ui/MainWindow.py`) owns the main thread. `core/Supervisor.py` runs one asyncio event loop on a worker thread; everything that captures, reads pixels or sends input runs there. The UI only calls the Supervisor's thread-safe methods (`select_client`, `start_feature`, `stop_feature`, `start_all`, `stop_all`, `apply_settings`, `detect_now`) and reads its immutable `StatusSnapshot` each frame.

**Detection (`detection/`, pure, no screen access)**: `LayoutDetector.detect_layout(image, templates, config)` returns a `Layout` with an entry for every `ComponentType`. It finds a common UI scale with the heart anchor, matches small anchor templates from `images/ui/` in grayscale, and derives each region from the anchor plus `config.geometry` (anchor-relative, at scale 1.0). The game view is the largest 15:11 rectangle; tile size = width / 15 and the character is on tile (7, 5). `recheck_layout` re-matches anchors near their known positions. `Readers.py` turns a component crop into a value (`bar_percent`, `battle_entries`, `chase_state`, `hunger_present`, `loot_message_present`, `find_mark`, `is_arrived`).

**Core (`core/`)**: `ClientWindow.find_client_windows` keeps visible windows whose title starts with `Tibia` and whose process is the official `client.exe` (Win32 calls behind a `Win32Api` object tests replace). `ScreenCapture` grabs client-area regions with `mss`. `GameInput` refuses input unless the client is the foreground window. `LayoutMonitor` polls the window and asks for detection when it moves, resizes, is restored, or a feature reports a mismatch; while anything is missing it retries full detection periodically, otherwise it re-checks anchors.

**Features (`modules/`)**: each feature class has `key`, `label`, `requires(settings)` and `async run(ctx)`; see `specs/001-auto-detect-layout-ui/contracts/feature-interface.md`. Each pass starts with `await ctx.ready()` (which pauses the feature with a reason while the client is not selected/visible/focused or a required component is missing) and ends with `await ctx.sleep(...)`. Positions come only from `ctx.layout`; settings are read from `ctx.settings` every pass. Never use `time.sleep`, coordinate literals or bare `except:` in `modules/` (`tests/test_Principles.py` enforces this).

**Config (`config/`)**: `Settings.py` holds frozen dataclasses for everything the user edits (hotkeys, thresholds in percent, timings, route, enabled features, last client) and `SettingsStore`, which saves `./settings.json` atomically and renames a damaged file to `settings.json.bad`. `DetectionConfig.py` holds detection constants (template names, anchor geometry, colours, thresholds); `get(name)` raises `KeyError` for unknown names. Values marked `# Measure (T022)` are placeholders until measured on real fixtures.

**Waypoint data (`data/*.json`)**: each file has the form `{"waypoints": [<image path>, ...]}`, each a mark icon from `images/marks/` placed on the in-game minimap. The walk feature visits them in order and wraps to the first; `Waypoints.list_routes()` reports routes with missing marks as invalid.

**Tests (`tests/`)**: no test touches the real screen or game. `tests/fakes.py` provides fake Win32, capture, input, detector and `FakeContext` for features; `tests/synthetic.py` builds synthetic client captures from random-texture anchors. Tests on real client captures (`client_*.png` + `*.expected.json`) skip until those fixtures exist. Constructors must not touch the screen.
