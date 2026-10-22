import json
import os
import tempfile
from unittest import TestCase

from config.Settings import Settings, SettingsStore, validate


class TestSettings(TestCase):

    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.path = os.path.join(self.dir.name, 'settings.json')
        self.store = SettingsStore(self.path)

    def tearDown(self):
        self.dir.cleanup()

    def write(self, data):
        with open(self.path, 'w', encoding='utf-8') as file:
            file.write(data if isinstance(data, str) else json.dumps(data))

    def test_missing_file_gives_defaults_without_warning(self):
        settings, warnings = self.store.load()
        self.assertEqual(settings, Settings())
        self.assertEqual(warnings, [])
        self.assertEqual(settings.hotkeys.attack, 'f1')
        self.assertEqual(settings.hotkeys.spell_aoe, 'del')

    def test_round_trip(self):
        changed = Settings().with_group('healing', low_hp_percent=30).with_feature_enabled('eating', True)
        self.store.save(changed)
        loaded, warnings = self.store.load()
        self.assertEqual(loaded, changed)
        self.assertEqual(warnings, [])
        self.assertFalse(os.path.exists(self.path + '.tmp'))

    def test_invalid_json_is_kept_as_bad_and_defaults_used(self):
        self.write('{not json')
        settings, warnings = self.store.load()
        self.assertEqual(settings, Settings())
        self.assertEqual(len(warnings), 1)
        self.assertTrue(os.path.exists(self.path + '.bad'))
        self.assertFalse(os.path.exists(self.path))

    def test_unknown_version_is_treated_as_damaged(self):
        self.write({'version': 99})
        settings, warnings = self.store.load()
        self.assertEqual(settings, Settings())
        self.assertTrue(os.path.exists(self.path + '.bad'))

    def test_single_invalid_field_falls_back(self):
        data = Settings().to_dict()
        data['healing']['low_hp_percent'] = 120
        data['mana']['refill_below_percent'] = 40
        self.write(data)
        settings, warnings = self.store.load()
        self.assertEqual(settings.healing.low_hp_percent, 45)
        self.assertEqual(settings.mana.refill_below_percent, 40)
        self.assertTrue(any('healing.low_hp_percent' in w for w in warnings))

    def test_low_must_be_below_high(self):
        data = Settings().to_dict()
        data['healing'] = {'low_hp_percent': 80, 'high_hp_percent': 70}
        self.write(data)
        settings, warnings = self.store.load()
        self.assertEqual(settings.healing, Settings().healing)
        self.assertTrue(warnings)
        self.assertTrue(validate(Settings().with_group('healing', low_hp_percent=85, high_hp_percent=85)))

    def test_unknown_keys_ignored_with_warning(self):
        data = Settings().to_dict()
        data['hotkeys']['jump'] = 'space'
        data['extra'] = 1
        self.write(data)
        settings, warnings = self.store.load()
        self.assertFalse(hasattr(settings.hotkeys, 'jump'))
        self.assertEqual(len(warnings), 2)

    def test_invalid_hotkey_falls_back(self):
        data = Settings().to_dict()
        data['hotkeys']['attack'] = 'not-a-key'
        data['hotkeys']['food'] = 'F9'
        self.write(data)
        settings, warnings = self.store.load()
        self.assertEqual(settings.hotkeys.attack, 'f1')
        self.assertEqual(settings.hotkeys.food, 'f9')

    def test_missing_keys_use_defaults(self):
        self.write({'version': 1, 'mana': {'refill_below_percent': 50}})
        settings, warnings = self.store.load()
        self.assertEqual(settings.mana.refill_below_percent, 50)
        self.assertEqual(settings.healing, Settings().healing)
        self.assertEqual(warnings, [])

    def test_misspelt_attribute_raises(self):
        with self.assertRaises(AttributeError):
            Settings().healing.low_hp_precent

    def test_defaults_are_valid(self):
        self.assertEqual(validate(Settings()), [])
