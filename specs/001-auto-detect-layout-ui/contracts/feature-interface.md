# Contract: Feature Interface

Every automated behaviour in `modules/` implements this contract. The Supervisor
(`core/Supervisor.py`) is the only caller.

## Shape

```python
class Feature(Protocol):
    key: str                                  # e.g. "healing"
    label: str                                # e.g. "Healing"

    def requires(self, settings: Settings) -> frozenset[ComponentType]:
        """Components needed to act (data-model.md); may depend on settings, e.g. eating"""

    async def run(self, ctx: FeatureContext) -> None:
        """Loop until cancelled. One pass per iteration."""
```

```python
class FeatureContext(Protocol):
    @property
    def layout(self) -> Layout: ...           # current snapshot; may change between passes
    @property
    def settings(self) -> Settings: ...       # current snapshot; may change between passes
    async def ready(self) -> None: ...        # returns when the feature may act (see below)
    async def sleep(self, seconds: float) -> None: ...
    async def wait(self, reason: str, seconds: float = 0.5) -> None: ...  # pause for a feature's own reason
    def is_running(self, key: str) -> bool: ...  # another feature is running (not paused or off)
    def capture(self, component: ComponentType) -> np.ndarray: ...   # BGR image of the region
    def template(self, name: str) -> np.ndarray: ...  # images/ui template at the current UI scale
    def mark(self, path: str) -> np.ndarray: ...      # waypoint mark at the current UI scale
    async def press(self, key: str) -> bool: ...   # via GameInput; False + pause if not focused
    async def click(self, client_point: tuple[int, int], button: str = "left",
                    modifier: str | None = None) -> bool: ...
    def report_mismatch(self, component: ComponentType, reason: str) -> None: ...
    def log(self, message: str, level: str = "info") -> None: ...
```

## Rules

1. **One `await` per pass (Principle I).** Every path through one iteration of the loop in
   `run` awaits at least once: `await ctx.ready()` at the top and `await ctx.sleep(...)` at the
   end. Blocking work per pass stays under 100 ms.
2. **Ready gate (FR-008, FR-009).** Each pass starts with `await ctx.ready()`. It returns only
   when the client is selected, visible and in the foreground, and `ctx.layout.has(*requires)`.
   Until then the Supervisor shows the feature as `paused` with the reason.
3. **Positions only from the layout (Principle II).** A feature never uses a literal screen or
   client coordinate. Points come from `ctx.layout` (component regions, `tile_point`) or from
   readers applied to `ctx.capture(...)`.
4. **Settings are read each pass.** A feature reads thresholds and hotkeys from `ctx.settings`
   inside the loop, never caches them in `__init__`, so UI changes apply on the next pass
   (FR-020).
5. **Cancellation.** Stop cancels the task. A feature does not swallow `asyncio.CancelledError`.
   Anything that holds state in the game (for example Shift held while looting) is released in a
   `finally` block.
6. **Mismatch.** When a reader returns an impossible value (bar percent outside 0–100, mark
   region empty), the feature calls `ctx.report_mismatch(...)` and skips the pass. The
   `LayoutMonitor` re-detects (R10).
7. **Errors.** A feature catches only the specific errors it can recover from and logs each
   recovery with `ctx.log`. Bare `except:` is not allowed (Principle VI). Any other exception
   ends the task; the Supervisor logs it and sets the feature to `off`.
8. **Constructors are pure.** `__init__` takes no screen, window or input action, so tests can
   create features at import time (Principle IV).

## Feature list

| Key | Module | Behaviour (unchanged intent from today) |
|-----|--------|------------------------------------------|
| `healing` | `modules/Healing.py` | Below `low_hp_percent` press `heal_low`; else below `high_hp_percent` press `heal_high` |
| `mana_refill` | `modules/Healing.py` | Below `refill_below_percent` press `mana` |
| `eating` | `modules/Utils.py` | Press `food` every random interval in `[interval_min_s, interval_max_s]`; if `when_hungry`, only when the hunger icon is present |
| `chase` | `modules/Utils.py` | If chase is off, press `chase` |
| `attack_spells` | `modules/AttackSpells.py` | Targeted monster and fewer than `aoe_min_monsters`: single spells; otherwise AoE spells; then cool down |
| `attack` | `modules/CaveBot.py` | Untargeted monster in battle list: press `attack`, wait until target is gone |
| `loot` | `modules/CaveBot.py` | After a kill (the battle list's target frame disappears), if the loot message is present, shift+right-click the 9 tiles around the character in random order |
| `walk` | `modules/CaveBot.py` | No monsters: click the current route mark on the minimap; advance when within `arrival_radius_percent` of the centre; on "mark not found" press `refresh_map` once and log it |

`mana_refill` was previously part of `primary_healing`. It becomes its own feature so it can be
started and stopped separately. Today's rule is kept: when mana is below the refill threshold,
mana is refilled instead of casting a heal (a heal needs mana). So `healing` skips its pass while
`mana_refill` is running and mana is below `refill_below_percent`; if `mana_refill` is off,
`healing` heals regardless of mana.
