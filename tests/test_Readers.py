import json
import os
import unittest
from unittest import TestCase

import numpy as np

from config.DetectionConfig import DetectionConfig
from detection.Components import ComponentType, DetectedComponent, Region
from detection.LayoutDetector import TemplateDetector
from detection.Readers import (battle_entries, bar_percent, chase_on, chase_state, find_mark, hunger_present,
                               is_arrived, loot_message_present)
from detection.Templates import read_image
from tests.fakes import make_layout
from tests.synthetic import make_bar, make_battle, make_minimap, make_templates


C = ComponentType


class TestBarPercent(TestCase):

    def test_levels(self):
        for percent in (0, 10, 45, 85, 100):
            self.assertAlmostEqual(bar_percent(make_bar(percent)), percent, delta=1)

    def test_any_saturated_colour_counts(self):
        # Health turns yellow and red as it drops; mana is blue
        for colour in ((0, 200, 0), (0, 200, 220), (0, 0, 220), (200, 80, 0)):
            self.assertAlmostEqual(bar_percent(make_bar(60, colour=colour)), 60, delta=1)

    def test_thin_left_border(self):
        bar = make_bar(50)
        bar[:, 0] = 20
        self.assertAlmostEqual(bar_percent(bar), 50, delta=1)

    def test_scaled_bar(self):
        self.assertAlmostEqual(bar_percent(make_bar(30, width=225, height=20)), 30, delta=1)

    def test_empty_crop(self):
        with self.assertRaises(ValueError):
            bar_percent(np.zeros((0, 0, 3), np.uint8))


class TestBattleEntries(TestCase):

    def test_counts_and_target(self):
        self.assertEqual(battle_entries(make_battle(0)).count, 0)
        state = battle_entries(make_battle(3, targeted=True))
        self.assertEqual((state.count, state.targeted), (3, True))
        state = battle_entries(make_battle(1, targeted=False))
        self.assertEqual((state.count, state.targeted), (1, False))

    def test_scaled_rows(self):
        state = battle_entries(make_battle(2, row_height=33), scale=1.5)
        self.assertEqual(state.count, 2)


class TestChase(TestCase):

    def test_from_layout(self):
        layout = make_layout(detail={C.COMBAT_CONTROLS: {'chase_on': True}})
        self.assertTrue(chase_on(layout))
        with self.assertRaises(KeyError):
            chase_on(make_layout(found=set()))

    def test_live_state(self):
        images = make_templates()
        on, off = images['chase_on.png'], images['chase_off.png']
        self.assertTrue(chase_state(on, on, off))
        self.assertFalse(chase_state(off, on, off))
        self.assertIsNone(chase_state(np.full_like(on, 90), on, off))


class TestHunger(TestCase):

    def test_hunger_icon(self):
        hunger = make_templates()['hunger.png']
        strip = np.full((12, 100, 3), 60, np.uint8)
        self.assertFalse(hunger_present(strip, hunger))
        strip[1:11, 40:50] = hunger
        self.assertTrue(hunger_present(strip, hunger))


class TestLootMessage(TestCase):
    """ The fixtures from the old CaveBot loot tests """

    def test_loot_found(self):
        self.assertTrue(loot_message_present(read_image('tests/testdata/loot_found.png')))

    def test_no_loot(self):
        self.assertFalse(loot_message_present(read_image('tests/testdata/empty_loot.png')))


class TestMarks(TestCase):

    def setUp(self):
        self.mark = read_image('images/marks/checkmark.png')

    def test_find_mark(self):
        minimap = make_minimap(self.mark, at=(30, 70))
        point = find_mark(minimap, self.mark)
        self.assertIsNotNone(point)
        self.assertLessEqual(abs(point[0] - 30), 1)
        self.assertLessEqual(abs(point[1] - 70), 1)

    def test_mark_not_on_map(self):
        self.assertIsNone(find_mark(make_minimap(self.mark), self.mark))

    def test_is_arrived(self):
        size = (106, 109)
        self.assertTrue(is_arrived((53, 54), size, 6))
        self.assertTrue(is_arrived((57, 57), size, 6))
        self.assertFalse(is_arrived((70, 54), size, 6))
        self.assertTrue(is_arrived((70, 54), size, 20))


FIXTURES = ['client_800x600', 'client_1920x1080', 'client_1920x1080_125']


def have_fixtures():
    paths = [f"tests/testdata/{n}{ext}" for n in FIXTURES for ext in ('.png', '.expected.json')]
    templates = [os.path.join('images/ui', n) for n in DetectionConfig().template_files()]
    return all(os.path.isfile(p) for p in paths + templates)


@unittest.skipUnless(have_fixtures(), 'real client fixtures not captured yet (tasks T019-T021)')
class TestReadersOnRealFixtures(TestCase):
    """ T032/T041 checks on captures of the official client, using the expected JSON values """

    def setUp(self):
        self.detector = TemplateDetector(DetectionConfig())

    def load(self, name):
        image = read_image(f"tests/testdata/{name}.png")
        with open(f"tests/testdata/{name}.expected.json", encoding='utf-8') as file:
            expected = json.load(file)
        return image, expected

    def crop(self, image, expected, component_type):
        return Region(*expected[component_type.name]['region']).crop(image)

    def test_bars(self):
        for name in FIXTURES:
            with self.subTest(name):
                image, expected = self.load(name)
                self.assertAlmostEqual(bar_percent(self.crop(image, expected, C.HEALTH_BAR)),
                                       expected['health_percent'], delta=3)
                self.assertAlmostEqual(bar_percent(self.crop(image, expected, C.MANA_BAR)),
                                       expected['mana_percent'], delta=3)

    def test_battle_list_and_chase(self):
        for name in FIXTURES:
            with self.subTest(name):
                image, expected = self.load(name)
                layout = self.detector.detect(image)
                state = battle_entries(self.crop(image, expected, C.BATTLE_LIST), layout.scale)
                self.assertEqual(state.count, expected['battle_count'])
                self.assertEqual(state.targeted, expected['battle_targeted'])
                self.assertEqual(chase_on(layout), expected['chase_on'])
