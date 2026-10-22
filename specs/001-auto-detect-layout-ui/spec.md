# Feature Specification: Auto-Detected Layout and Management UI

**Feature Branch**: `001-auto-detect-layout-ui`

**Created**: 2026-10-22

**Status**: Draft

**Input**: User description: "We need to be building a bot which auto detects the Tibia window and
auto detects components on the screen, no matter what resolution, and adapts everything based on
that. There's a UI to manage everything." (`/speckit-specify` was run with no arguments; this
description comes from the constitution v2.0.0 amendment request in the same session.)

## Clarifications

### Session 2026-10-22

- Q: Which Tibia client should the bot detect and control? → A: Only the official current Tibia
  client (CipSoft), default layout.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Bot finds the game window and its components by itself (Priority: P1)

The player opens the Tibia client at whatever window size and screen resolution they like, then
starts the bot. Without any calibration, the bot finds the client window and locates the parts of
the game interface it relies on: health bar, mana bar, minimap, game view with the character
position, chat/server log, battle list, and status icons (such as hunger). The UI shows which of
these were found.

**Why this priority**: Every feature (healing, looting, walking, attacking) depends on knowing
where these components are. Without detection nothing else works at a resolution other than
800x600.

**Independent Test**: Open the client at two different window sizes, start detection from the UI,
and confirm the UI reports the window and every component as found, with a preview that marks each
detected region in the right place.

**Acceptance Scenarios**:

1. **Given** the Tibia client is open at any supported window size, **When** the user starts
   detection, **Then** the UI shows the client window as found and lists each required component
   as found within 5 seconds.
2. **Given** detection succeeded, **When** the user opens the detection preview, **Then** each
   detected component is outlined on a capture of the client and every outline covers its
   component.
3. **Given** the Tibia client is not running, **When** the user starts detection, **Then** the UI
   reports that no client window was found and no feature can be started.
4. **Given** one component (for example, the battle list) is hidden in the client, **When**
   detection runs, **Then** the UI reports that component as missing and lists which features
   cannot run without it, while the other components are still reported as found.

---

### User Story 2 - Features keep working when the window changes (Priority: P1)

While the bot is running, the player moves, resizes, or maximizes the client window, or rearranges
its side panels. The bot notices, finds the components again, and carries on using the new
positions. If a component it needs disappears, the affected feature pauses instead of clicking in
the wrong place.

**Why this priority**: A bot that keeps acting on old positions clicks and casts in the wrong
places, which is worse than not acting at all.

**Independent Test**: Start healing, resize the client window, and confirm healing still reacts to
low health at the new size; then cover the health bar and confirm healing pauses and the UI says
why.

**Acceptance Scenarios**:

1. **Given** features are running, **When** the user moves or resizes the client window,
   **Then** the bot re-detects the layout within 3 seconds and running features continue at the
   new positions.
2. **Given** a running feature needs a component, **When** that component can no longer be
   found, **Then** the feature pauses, performs no clicks or key presses, and the UI shows it as
   paused with the reason.
3. **Given** a feature was paused because a component was missing, **When** the component is
   found again, **Then** the feature resumes automatically and the UI shows it as running.
4. **Given** the client window is minimized or closed, **When** the bot checks the window,
   **Then** every feature pauses and the UI reports the window as lost.

---

### User Story 3 - Manage everything from the UI (Priority: P2)

From one control window, the player starts and stops the whole bot or any single feature
(healing, mana refill, eating, attack spells, auto chase, attacking, looting, waypoint walking),
picks a waypoint route, and changes settings such as hotkeys and health/mana thresholds. Settings
are kept between sessions.

**Why this priority**: Detection removes calibration, but the player still needs a way to control
the bot without editing files. Today the bot cannot be stopped once started.

**Independent Test**: Enable healing and eating, start them, stop eating only, change the healing
threshold, restart the application, and confirm the threshold change was kept and eating stays off.

**Acceptance Scenarios**:

1. **Given** the bot is idle, **When** the user enables a feature and presses Start, **Then** only
   the enabled features begin acting in the game.
2. **Given** several features are running, **When** the user stops one feature, **Then** that
   feature stops acting within 1 second and the others keep running.
3. **Given** the bot is running, **When** the user presses Stop, **Then** all features stop acting
   within 1 second and the UI stays responsive.
4. **Given** the user changes a hotkey or threshold, **When** they save it, **Then** the running
   bot uses the new value without a restart, and the value is still set after the application is
   reopened.
5. **Given** the user selects a waypoint route, **When** waypoint walking starts, **Then** the bot
   walks that route in order and the UI shows which route is active.

---

### User Story 4 - See what the bot is doing (Priority: P3)

While the bot runs, the player can see each feature's state (off, running, paused and why), the
detection status, and a short log of recent actions and problems, so they can tell at a glance
whether the bot is working.

**Why this priority**: Useful for trust and troubleshooting, but the bot works without it.

**Independent Test**: Run healing and walking, block a waypoint icon, and confirm the UI log shows
the failed waypoint search and the recovery attempt.

**Acceptance Scenarios**:

1. **Given** the bot is running, **When** a feature performs a recovery action or hits a
   detection failure, **Then** the UI log shows an entry with the time, the feature, and what
   happened.
2. **Given** the bot is running, **When** the user looks at the control window, **Then** each
   feature's current state is visible without opening another screen.

---

### Edge Cases

- More than one Tibia client is open: the UI lists them and the user picks which one the bot
  controls; until a choice is made no feature starts.
- The client window is partly off-screen or covered by another window: components that cannot be
  seen are reported as missing and dependent features pause.
- The client runs on a secondary monitor or with display scaling other than 100%: detection and
  clicks still land on the right components.
- The window is very small, so components are tiny or hidden by the client: the UI reports
  which components are missing instead of guessing.
- The user changes settings while features are running: changes apply on the next loop pass
  without dropping the bot into an inconsistent state.
- A saved settings file is missing or damaged: the bot starts with default settings and tells the
  user the saved settings could not be loaded.
- The bot's own control window covers part of the client: detection ignores the control window
  and the user is warned that the client is obscured.

## Requirements *(mandatory)*

### Functional Requirements

**Window and component detection**

- **FR-001**: The system MUST find the official Tibia client window automatically, without the
  user entering coordinates or a resolution. Windows of other clients (such as OpenTibia-based
  clients) MUST NOT be offered for control.
- **FR-002**: When more than one client window is open, the system MUST let the user choose which
  one to control.
- **FR-003**: The system MUST detect these client components: health bar, mana bar, minimap, game
  view and character position, chat/server log, battle list, and status icons (including hunger).
- **FR-004**: Detection MUST work at any client window size and screen resolution at which the
  client itself shows those components, and with display scaling other than 100%.
- **FR-005**: Every screen position the bot reads from or clicks on MUST be derived from the most
  recent detection result.
- **FR-006**: The system MUST re-run detection when the client window moves, resizes, is
  minimized or restored, or when a detected component stops matching what is on screen.
- **FR-007**: The system MUST report, for each component, whether it is currently found or
  missing.

**Safe behaviour on failure**

- **FR-008**: Each feature MUST declare which components it needs, and MUST pause while any of
  them is missing.
- **FR-009**: A paused feature MUST NOT click, move the mouse, or press keys.
- **FR-010**: A feature paused for a missing component MUST resume automatically once the
  component is detected again.
- **FR-011**: The system MUST record every detection failure, pause, resume, and recovery action
  with a time and the feature involved.

**Management UI**

- **FR-012**: The UI MUST let the user start and stop the whole bot and each feature
  individually, at any time, without closing the application.
- **FR-013**: The UI MUST stay responsive while features are running.
- **FR-014**: The UI MUST show the detection status (window found or not, each component found or
  missing) and offer a preview that marks the detected regions on a capture of the client.
- **FR-015**: The UI MUST show each feature's state: off, running, or paused with its reason.
- **FR-016**: The UI MUST let the user edit hotkeys for every in-game action the bot uses.
- **FR-017**: The UI MUST let the user edit feature thresholds and timings, at minimum: the health
  percentages for each healing level, the mana percentage for mana refill, the eating interval, and
  the attack-spell conditions.
- **FR-018**: The UI MUST let the user pick a waypoint route from the saved routes and show the
  active one.
- **FR-019**: The UI MUST show a log of recent entries from FR-011.
- **FR-020**: Changed settings MUST take effect for running features without restarting them.

**Settings**

- **FR-021**: The system MUST save all user settings and restore them when the application starts.
- **FR-022**: Thresholds MUST be stored as percentages or relative positions within a component,
  never as screen coordinates, so they stay valid when the window size changes.
- **FR-023**: If saved settings cannot be read, the system MUST start with defaults and tell the
  user.
- **FR-024**: Existing waypoint routes in the current saved format MUST keep working.

**Existing features**

- **FR-025**: Healing, mana refill, eating, attack spells, auto chase, monster attacking, looting,
  and waypoint walking MUST all work using detected positions, at least as well as they work today
  at 800x600.

### Key Entities

- **Client Window**: One running Tibia client the bot can control. Has a title, its current
  position and size on screen, and whether it is visible, minimized, or lost.
- **Detected Component**: A part of the client interface (health bar, minimap, and so on). Has a
  type, its current region inside the client window, whether it is found, and when it was last
  confirmed.
- **Layout**: The full set of detected components for one client window at one moment. Replaced
  whenever detection runs again.
- **Feature**: One automated behaviour (healing, looting, walking, ...). Has an on/off choice from
  the user, a current state (off, running, paused), a pause reason, and the list of components it
  needs.
- **Settings**: Everything the user can change: hotkeys, thresholds, timings, selected route, and
  selected client. Saved between sessions.
- **Waypoint Route**: An ordered list of minimap marks the bot walks through, wrapping back to the
  first.
- **Activity Log Entry**: A time, a feature (or "detection"), and a short description of what
  happened.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A new user can go from opening the application to a running healing feature in under
  2 minutes, with no manual calibration.
- **SC-002**: Detection finds the client window and all required components on the first attempt
  in at least 95% of tries across at least three different window sizes, including 800x600 and a
  maximized window on a 1920x1080 screen.
- **SC-003**: After the client window is moved or resized, features resume correct operation within
  3 seconds.
- **SC-004**: When a needed component is missing, the bot performs zero clicks or key presses for
  the affected feature.
- **SC-005**: Stopping a single feature or the whole bot takes effect within 1 second, every time.
- **SC-006**: Every setting a user needs for normal play can be changed in the UI; normal use
  requires editing zero files by hand.
- **SC-007**: Settings changed in the UI are still in effect after restarting the application, in
  100% of restarts with an intact settings file.
- **SC-008**: Every existing feature behaves at least as reliably at a non-800x600 size as it does
  today at 800x600, judged by the same play test (for example, healing triggers at the configured
  threshold every time during a 10-minute session).

## Assumptions

- The target is only the official current Tibia desktop client (CipSoft) on Windows, as
  clarified; OpenTibia-based clients are out of scope and may be added by a later feature.
- The client's default interface layout and theme are used; heavily customised layouts may need a
  follow-up feature.
- The user runs one bot instance controlling one client at a time; controlling several clients at
  once is out of scope.
- The required components are visible in the client (not closed by the user); a missing component
  is reported, not worked around.
- The existing minimap-mark waypoint routes and their saved format remain the way routes are
  defined; a route editor is out of scope beyond selecting a route.
- The control window may stay on top of other windows, but the user is expected to keep it from
  covering the client.
- The bot keeps running on Windows on the same machine as the client; tooling choices are left
  to the plan.
- Users are responsible for complying with the game's terms of service.
