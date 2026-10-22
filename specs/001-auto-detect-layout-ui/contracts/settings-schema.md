# Contract: Settings File (`settings.json`)

Location: `./settings.json` at the repository root (run from the root, per the constitution).
Git-ignored. Written only by `SettingsStore` in `config/Settings.py`.

## Example (defaults)

```json
{
  "version": 1,
  "client": { "last_title": null },
  "hotkeys": {
    "attack": "f1",
    "chase": "f12",
    "heal_high": "f8",
    "heal_low": "f4",
    "mana": "f7",
    "food": "f5",
    "spell_single": "f2",
    "spell_single_2": "f3",
    "spell_aoe": "del",
    "spell_aoe_strong": "end",
    "refresh_map": "f6"
  },
  "healing": { "high_hp_percent": 85, "low_hp_percent": 45 },
  "mana": { "refill_below_percent": 60 },
  "eating": { "interval_min_s": 20.3, "interval_max_s": 30.7, "when_hungry": false },
  "attack_spells": { "aoe_min_monsters": 3, "cooldown_min_s": 2.3, "cooldown_max_s": 2.8 },
  "cavebot": { "route": null, "arrival_radius_percent": 6 },
  "features": {
    "enabled": {
      "healing": false, "mana_refill": false, "eating": false, "attack_spells": false,
      "chase": false, "attack": false, "loot": false, "walk": false
    }
  }
}
```

## Validation

| Field | Rule |
|-------|------|
| `version` | Integer; `1` for this feature. Higher unknown versions are treated as damaged |
| `hotkeys.*` | Non-empty string that `pyautogui` accepts as a key name (checked against `pyautogui.KEYBOARD_KEYS`, lower-cased) |
| `healing.low_hp_percent`, `healing.high_hp_percent` | Integers 1–99, `low < high` |
| `mana.refill_below_percent` | Integer 1–99 |
| `eating.interval_min_s`, `interval_max_s` | Numbers ≥ 1, `min ≤ max` |
| `attack_spells.aoe_min_monsters` | Integer 2–8 |
| `attack_spells.cooldown_min_s`, `cooldown_max_s` | Numbers ≥ 0.5, `min ≤ max` |
| `cavebot.route` | Null or a file name that exists in `data/` |
| `cavebot.arrival_radius_percent` | Integer 1–25 |
| `features.enabled.*` | Boolean; keys must be known feature keys |
| `client.last_title` | Null or string |

## Load behaviour

1. File missing → defaults, no warning (first run).
2. File unreadable, not valid JSON, or failing validation as a whole → rename to
   `settings.json.bad` (replacing an older one), use defaults, log a warning shown in the UI
   (FR-023).
3. A single invalid field → use the default for that field, keep the rest, log a warning naming
   the field.
4. Unknown keys → ignored, warning logged, removed on the next save.
5. Missing keys (older file) → defaults for those keys.

## Save behaviour

- Saved when the user presses Save in the Settings tab and when a feature's enabled flag or the
  route changes.
- Written to `settings.json.tmp` then renamed over `settings.json` (atomic on the same volume).
- Saving never blocks the bot thread; the UI thread writes the file.

## Programmatic access

`Settings` is a frozen dataclass tree. Code reads `settings.healing.low_hp_percent`; a misspelt
attribute raises `AttributeError` (Principle III). The UI builds a new `Settings` with
`dataclasses.replace` and passes it to `Supervisor.apply_settings`, which swaps it atomically so
features see it on their next pass.
