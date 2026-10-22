# Quickstart: Validate Auto-Detected Layout and Management UI

How to prove the feature works end to end. Contracts: [feature-interface](./contracts/feature-interface.md),
[layout-detector](./contracts/layout-detector.md), [settings-schema](./contracts/settings-schema.md),
[ui-controls](./contracts/ui-controls.md). Entities: [data-model.md](./data-model.md).

## Prerequisites

- Windows 10/11, Python 3.13.
- The official Tibia client installed and logged in to a character, default interface layout,
  with the battle list, minimap, health/mana bars and chat visible.
- Commands run from the repository root.

```powershell
python -m pip install -r requirements.txt
```

## 1. Automated checks (no game needed)

```powershell
python -m unittest discover -v -s ./tests -p "test_*.py"
```

Expected: all tests pass, including:

- `test_LayoutDetector`: every component found in `client_800x600.png` and
  `client_1920x1080.png` within 3 px of the expected regions; `BATTLE_LIST` missing in
  `client_1920x1080_no_battle_list.png` while the rest are found.
- `test_Readers`: bar percentages, battle-list count/target, chase state, hunger, loot message
  and mark position read correctly from fixtures.
- `test_Settings`: defaults, save/load round trip, a damaged file becomes `settings.json.bad`
  and defaults are used.
- `test_Supervisor`: with fake features and layouts, a feature pauses when a component goes
  missing, sends no input while paused, resumes when it returns, and stops within 1 s.

## 2. Capture fixtures and templates (one-off, game needed)

Needed before step 1 can pass for the first time (research R13).

```powershell
python helpers/CaptureClient.py tests/testdata/client_1920x1080.png
```

Repeat with the client at 800x600, with the battle list closed, and at 125% display scaling.
Crop anchor templates from these captures into `images/ui/` and record the expected regions in
the matching `*.expected.json` files.

## 3. Manual validation with the game

Start the app:

```powershell
python App.py
```

| # | Steps | Expected | Spec |
|---|-------|----------|------|
| 1 | Client closed; open the app | "No Tibia client found"; Start All disabled | US1-3 |
| 2 | Start the client windowed at about 1024x768; wait | Client appears and is selected; Detection tab shows all components Found within 5 s; preview outlines line up with the components | US1-1, US1-2, SC-002 |
| 3 | Close the battle list in the client; press Detect now | Battle list Missing; table lists Attack, Attack spells, Walk as affected; others Found | US1-4 |
| 4 | Enable Healing; Start All; lose HP below the low threshold | Heal-low hotkey is pressed; Run tab shows Healing Running | US3-1 |
| 5 | While healing runs, maximize the client | Within 3 s Detection shows a new detection; healing still triggers at the threshold | US2-1, SC-003 |
| 6 | Drag another window over the health bar | Healing shows `Paused: health bar not found`; no keys pressed; Log has an entry. Move the window away: Healing returns to Running | US2-2, US2-3, SC-004 |
| 7 | Click on the app window so the client loses focus | Features show `Paused: client not focused`; no keys reach the app window | R11 |
| 8 | Minimize the client | All features paused; client status Minimized | US2-4 |
| 9 | Enable Eating too; start it; then stop only Eating | Eating Off within 1 s; Healing keeps running | US3-2, SC-005 |
| 10 | Stop All | Everything Off within 1 s; UI stays responsive | US3-3 |
| 11 | Change the low-HP threshold and a hotkey; Save; close and reopen the app | New values shown and used | US3-4, SC-007 |
| 12 | Select route `3points.json`; enable Walk, Attack, Loot; Start All in a hunting area | Character walks the marks in order, attacks monsters, loots after kills; Run tab shows the route | US3-5, FR-025 |
| 13 | During step 12, hide a route mark on the minimap | Log shows "mark not found" and a single map refresh; walking continues when found | US4-1 |
| 14 | Replace `settings.json` with invalid text; open the app | Warning that settings could not be loaded; defaults shown; `settings.json.bad` exists | FR-023 |
| 15 | Repeat 2, 4 and 12 with the client at 800x600 and with display scaling at 125% | Same results | FR-004, SC-002, SC-008 |

## Done when

- Step 1 passes.
- Steps 1–15 behave as expected at a minimum of two window sizes (800x600 and maximized
  1920x1080).
- Normal play needed no edits to any file (SC-006).
