# Contract: Management UI (`ui/MainWindow.py`)

One always-on-top Dear PyGui 2.x viewport (default 420x560, resizable, position remembered
only for the session). The UI calls Supervisor methods and reads `StatusSnapshot`; it never
captures the screen or sends input itself.

## Header (always visible)

| Element | Behaviour |
|---------|-----------|
| Client selector (combo) | Lists found official clients by title. Empty → text "No Tibia client found" and Start disabled. One client → selected automatically. Several → none selected until the user picks one (pre-selects `client.last_title` if it matches) |
| Client status | `Found`, `Minimized`, `Not focused`, `Lost` |
| Start All / Stop All | Start All starts every enabled feature; Stop All stops every feature within 1 s. The button shows Stop All while any feature is running or paused |

## Run tab

One row per feature (8 rows, in the order of the feature list in
[feature-interface.md](./feature-interface.md)):

| Column | Behaviour |
|--------|-----------|
| Enabled (checkbox) | Saved to settings. Unchecking a running feature stops it |
| Name | Feature label |
| State | `Off`, `Running`, `Paused: <reason>` (for example `Paused: battle list not found`) |
| Start / Stop button | Starts or stops just this feature. Disabled when no client is selected |

Route selector (combo) under the `walk` row: files in `data/`, with the active route shown. A
route with a missing mark image is shown as `<name> (invalid)` and cannot be selected.

## Detection tab

| Element | Behaviour |
|---------|-----------|
| Component table | One row per `ComponentType`: Found / Missing, reason, score, region size; lists the features that need each missing component |
| Detect now (button) | Forces a full re-detection |
| Preview | Shows the latest client capture scaled to fit, with an outline and label for each found component. Refreshes on each new Layout and when Detect now is pressed. Not refreshed continuously, to save CPU |
| Last detection | Time and how long it took |

## Settings tab

Grouped inputs for every field in [settings-schema.md](./settings-schema.md) except
`version` and `features`:

- Hotkeys: one text input per hotkey; invalid key names are shown in red and block Save.
- Healing, Mana, Eating, Attack spells, Cavebot: numeric inputs with the ranges from the schema.
- Save button: validates, writes the file, and applies to running features (FR-020).
- Revert button: discards unsaved edits.
- A warning line shows if the settings file was damaged and defaults were loaded (FR-023).

## Log tab

- Newest 100 `ActivityLogEntry` rows: time, source, level, message. Warnings and errors are
  coloured.
- Filter combo: All / one feature / detection.
- Clear button: clears the view only.

## Responsiveness rules

- No UI callback blocks for more than 50 ms: callbacks only call Supervisor methods (which
  schedule work on the bot thread) or write the settings file.
- The UI reads `StatusSnapshot` once per frame; it never waits for the bot thread.
- Closing the window calls Stop All, waits up to 2 s for tasks to finish, then exits.
