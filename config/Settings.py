import json
import os
from dataclasses import asdict, dataclass, field, fields, replace

import pyautogui


SETTINGS_VERSION = 1
FEATURE_KEYS = ('healing', 'mana_refill', 'eating', 'attack_spells', 'chase', 'attack', 'loot', 'walk')


@dataclass(frozen=True)
class Hotkeys:
    attack: str = 'f1'
    chase: str = 'f12'
    heal_high: str = 'f8'
    heal_low: str = 'f4'
    mana: str = 'f7'
    food: str = 'f5'
    spell_single: str = 'f2'
    spell_single_2: str = 'f3'
    spell_aoe: str = 'del'
    spell_aoe_strong: str = 'end'
    refresh_map: str = 'f6'


@dataclass(frozen=True)
class HealingSettings:
    high_hp_percent: int = 85
    low_hp_percent: int = 45


@dataclass(frozen=True)
class ManaSettings:
    refill_below_percent: int = 60


@dataclass(frozen=True)
class EatingSettings:
    interval_min_s: float = 20.3
    interval_max_s: float = 30.7
    when_hungry: bool = False


@dataclass(frozen=True)
class AttackSpellSettings:
    aoe_min_monsters: int = 3
    cooldown_min_s: float = 2.3
    cooldown_max_s: float = 2.8


@dataclass(frozen=True)
class CaveBotSettings:
    route: str | None = None
    arrival_radius_percent: int = 6


@dataclass(frozen=True)
class FeatureSettings:
    enabled: dict = field(default_factory=lambda: {key: False for key in FEATURE_KEYS})


@dataclass(frozen=True)
class ClientSettings:
    last_title: str | None = None


@dataclass(frozen=True)
class Settings:
    """ Everything the user can change from the UI """
    version: int = SETTINGS_VERSION
    client: ClientSettings = field(default_factory=ClientSettings)
    hotkeys: Hotkeys = field(default_factory=Hotkeys)
    healing: HealingSettings = field(default_factory=HealingSettings)
    mana: ManaSettings = field(default_factory=ManaSettings)
    eating: EatingSettings = field(default_factory=EatingSettings)
    attack_spells: AttackSpellSettings = field(default_factory=AttackSpellSettings)
    cavebot: CaveBotSettings = field(default_factory=CaveBotSettings)
    features: FeatureSettings = field(default_factory=FeatureSettings)

    def with_group(self, group, **values):
        """ Returns a copy with fields of one group replaced, e.g. with_group('healing', low_hp_percent=40) """
        return replace(self, **{group: replace(getattr(self, group), **values)})

    def with_feature_enabled(self, key, enabled):
        flags = dict(self.features.enabled)
        flags[key] = enabled
        return replace(self, features=FeatureSettings(enabled=flags))

    def to_dict(self):
        return asdict(self)


GROUPS = {
    'client': ClientSettings,
    'hotkeys': Hotkeys,
    'healing': HealingSettings,
    'mana': ManaSettings,
    'eating': EatingSettings,
    'attack_spells': AttackSpellSettings,
    'cavebot': CaveBotSettings,
}


def _is_number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _int_in(low, high):
    return lambda v: isinstance(v, int) and not isinstance(v, bool) and low <= v <= high


def _number_at_least(low):
    return lambda v: _is_number(v) and v >= low


def is_valid_key(value):
    return isinstance(value, str) and value.strip().lower() in pyautogui.KEYBOARD_KEYS


def _route_exists(value):
    return value is None or (isinstance(value, str) and os.path.isfile(os.path.join('./data', value)))


# Single-field rules: (group, field) -> (check, description shown to the user)
FIELD_RULES = {
    ('client', 'last_title'): (lambda v: v is None or isinstance(v, str), 'null or text'),
    ('healing', 'high_hp_percent'): (_int_in(1, 99), 'a whole number 1-99'),
    ('healing', 'low_hp_percent'): (_int_in(1, 99), 'a whole number 1-99'),
    ('mana', 'refill_below_percent'): (_int_in(1, 99), 'a whole number 1-99'),
    ('eating', 'interval_min_s'): (_number_at_least(1), 'a number of at least 1'),
    ('eating', 'interval_max_s'): (_number_at_least(1), 'a number of at least 1'),
    ('eating', 'when_hungry'): (lambda v: isinstance(v, bool), 'true or false'),
    ('attack_spells', 'aoe_min_monsters'): (_int_in(2, 8), 'a whole number 2-8'),
    ('attack_spells', 'cooldown_min_s'): (_number_at_least(0.5), 'a number of at least 0.5'),
    ('attack_spells', 'cooldown_max_s'): (_number_at_least(0.5), 'a number of at least 0.5'),
    ('cavebot', 'route'): (_route_exists, 'null or a file in data/'),
    ('cavebot', 'arrival_radius_percent'): (_int_in(1, 25), 'a whole number 1-25'),
}
for _name in (f.name for f in fields(Hotkeys)):
    FIELD_RULES[('hotkeys', _name)] = (is_valid_key, 'a key name pyautogui knows')

# Pairs that must satisfy first < second (strict) or first <= second
PAIR_RULES = [
    ('healing', 'low_hp_percent', 'high_hp_percent', True),
    ('eating', 'interval_min_s', 'interval_max_s', False),
    ('attack_spells', 'cooldown_min_s', 'cooldown_max_s', False),
]


def _pair_ok(low, high, strict):
    return low < high if strict else low <= high


def validate(settings):
    """ Returns a list of problems; empty when every value is valid """
    problems = []
    for (group, name), (check, description) in FIELD_RULES.items():
        value = getattr(getattr(settings, group), name)
        if not check(value):
            problems.append(f"{group}.{name} must be {description}")
    for group, low_name, high_name, strict in PAIR_RULES:
        values = getattr(settings, group)
        low, high = getattr(values, low_name), getattr(values, high_name)
        if _is_number(low) and _is_number(high) and not _pair_ok(low, high, strict):
            relation = '<' if strict else '<='
            problems.append(f"{group}.{low_name} must be {relation} {group}.{high_name}")
    for key, value in settings.features.enabled.items():
        if key not in FEATURE_KEYS or not isinstance(value, bool):
            problems.append(f"features.enabled.{key} must be a known feature set to true or false")
    return problems


def settings_from_dict(data):
    """ Builds Settings from parsed JSON. Invalid fields fall back to defaults with a warning """
    warnings = []
    defaults = Settings()
    groups = {}

    for group, cls in GROUPS.items():
        raw = data.get(group, {})
        default_group = getattr(defaults, group)
        if not isinstance(raw, dict):
            warnings.append(f"Settings group '{group}' is not an object; using defaults")
            groups[group] = default_group
            continue
        known = {f.name for f in fields(cls)}
        for unknown in sorted(set(raw) - known):
            warnings.append(f"Unknown setting '{group}.{unknown}' ignored")
        values = {}
        for name in known:
            value = raw.get(name, getattr(default_group, name))
            if group == 'hotkeys' and isinstance(value, str):
                value = value.strip().lower()
            check, description = FIELD_RULES[(group, name)]
            if not check(value):
                warnings.append(f"Setting '{group}.{name}' must be {description}; using default")
                value = getattr(default_group, name)
            values[name] = value
        groups[group] = cls(**values)

    for group, low_name, high_name, strict in PAIR_RULES:
        values = groups[group]
        if not _pair_ok(getattr(values, low_name), getattr(values, high_name), strict):
            default_group = getattr(defaults, group)
            warnings.append(f"Settings '{group}.{low_name}' and '{group}.{high_name}' conflict; using defaults")
            groups[group] = replace(values, **{low_name: getattr(default_group, low_name),
                                               high_name: getattr(default_group, high_name)})

    enabled = dict(defaults.features.enabled)
    raw_features = data.get('features', {})
    raw_enabled = raw_features.get('enabled', {}) if isinstance(raw_features, dict) else {}
    if isinstance(raw_enabled, dict):
        for key, value in raw_enabled.items():
            if key in FEATURE_KEYS and isinstance(value, bool):
                enabled[key] = value
            else:
                warnings.append(f"Setting 'features.enabled.{key}' ignored")

    for unknown in sorted(set(data) - set(GROUPS) - {'version', 'features'}):
        warnings.append(f"Unknown setting '{unknown}' ignored")

    return Settings(version=SETTINGS_VERSION, features=FeatureSettings(enabled=enabled), **groups), warnings


class SettingsStore:
    """ Loads and saves Settings as JSON """

    def __init__(self, path='./settings.json'):
        self.path = path

    def load(self):
        """ Returns (settings, warnings) """
        if not os.path.exists(self.path):
            return Settings(), []
        try:
            with open(self.path, encoding='utf-8') as file:
                data = json.load(file)
            if not isinstance(data, dict):
                raise ValueError('top level is not an object')
            if data.get('version') != SETTINGS_VERSION:
                raise ValueError(f"unsupported version {data.get('version')!r}")
        except (OSError, ValueError) as error:
            # json.JSONDecodeError and UnicodeDecodeError are ValueErrors
            bad_path = self.path + '.bad'
            os.replace(self.path, bad_path)
            return Settings(), [f"Settings could not be loaded ({error}); defaults are used and "
                                f"the old file was kept as {bad_path}"]
        return settings_from_dict(data)

    def save(self, settings):
        tmp_path = self.path + '.tmp'
        with open(tmp_path, 'w', encoding='utf-8') as file:
            json.dump(settings.to_dict(), file, indent=2)
        os.replace(tmp_path, self.path)
