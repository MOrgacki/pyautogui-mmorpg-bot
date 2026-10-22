import json
import os
import time
import unittest
from unittest import TestCase

import numpy as np

from config.DetectionConfig import DetectionConfig
from detection.Components import ComponentType
from detection.LayoutDetector import TemplateDetector, detect_layout, recheck_layout
from detection.Templates import read_image
from tests.synthetic import expected_region, make_client


C = ComponentType
ANCHOR_OF = {
    C.HEALTH_BAR: 'heart.png',
    C.MANA_BAR: 'mana.png',
    C.BATTLE_LIST: 'battle_list_title.png',
    C.MINIMAP: 'minimap_buttons.png',
    C.COMBAT_CONTROLS: 'chase_on.png',
    C.STATUS_ICONS: 'status_strip.png',
    C.CHAT: 'chat_tabs.png',
}


class TestDetectSynthetic(TestCase):
    """ Synthetic clients built from random-texture anchors (see tests/synthetic.py) """

    def assertRegionNear(self, region, expected, tolerance=3):
        self.assertIsNotNone(region)
        for actual, wanted in zip(region.as_list(), expected):
            self.assertLessEqual(abs(actual - wanted), tolerance, f"{region} vs {expected}")

    def check_client(self, size, scale, offset=(0, 0)):
        image, templates, anchors, game_view = make_client(size, scale, offset=offset)
        layout = detect_layout(image, templates, DetectionConfig(), window_hwnd=5, generation=3)
        self.assertEqual(layout.scale, scale)
        self.assertEqual(layout.client_size, size)
        self.assertEqual(layout.generation, 3)
        for component_type, name in ANCHOR_OF.items():
            component = layout.get(component_type)
            self.assertTrue(component.found, component_type)
            self.assertRegionNear(component.region, expected_region(anchors[name], component_type, scale))
        game = layout.get(C.GAME_VIEW)
        self.assertTrue(game.found)
        self.assertRegionNear(game.region, game_view)
        self.assertAlmostEqual(layout.tile_size, game_view[2] / 15, delta=0.5)
        return layout

    def test_800x600(self):
        self.check_client((800, 600), 1.0)

    def test_1920x1080(self):
        self.check_client((1920, 1080), 1.0, offset=(1000, 400))

    def test_1920x1080_at_125_percent(self):
        self.check_client((1920, 1080), 1.25, offset=(1000, 400))

    def test_missing_battle_list(self):
        image, templates, _, _ = make_client(omit=('battle_list_title.png',))
        layout = detect_layout(image, templates, DetectionConfig())
        self.assertFalse(layout.get(C.BATTLE_LIST).found)
        self.assertEqual(layout.get(C.BATTLE_LIST).missing_reason, 'anchor not found')
        for component_type in set(C) - {C.BATTLE_LIST}:
            self.assertTrue(layout.get(component_type).found, component_type)

    def test_chase_variant(self):
        image, templates, _, _ = make_client()
        self.assertTrue(detect_layout(image, templates, DetectionConfig()).get(C.COMBAT_CONTROLS).detail['chase_on'])
        image, templates, _, _ = make_client(chase='chase_off.png')
        self.assertFalse(detect_layout(image, templates, DetectionConfig()).get(C.COMBAT_CONTROLS).detail['chase_on'])

    def test_window_too_small(self):
        _, templates, _, _ = make_client()
        layout = detect_layout(np.zeros((8, 8, 3), np.uint8), templates, DetectionConfig())
        self.assertEqual(set(layout.components), set(C))
        self.assertTrue(all(c.missing_reason == 'window too small' for c in layout.components.values()))

    def test_invalid_image(self):
        _, templates, _, _ = make_client()
        for bad in (np.zeros((0, 0, 3), np.uint8), np.zeros((100, 100), np.uint8), None):
            with self.assertRaises(ValueError):
                detect_layout(bad, templates, DetectionConfig())

    def test_deterministic(self):
        image, templates, _, _ = make_client()
        first = detect_layout(image, templates, DetectionConfig())
        second = detect_layout(image, templates, DetectionConfig())
        self.assertEqual(first.components, second.components)

    def test_1920x1080_under_one_second(self):
        image, templates, _, _ = make_client((1920, 1080), 1.0, offset=(1000, 400))
        detect_layout(image, templates, DetectionConfig())
        started = time.perf_counter()
        detect_layout(image, templates, DetectionConfig())
        self.assertLess(time.perf_counter() - started, 1.0)

    def test_recheck(self):
        image, templates, _, _ = make_client()
        layout = detect_layout(image, templates, DetectionConfig())
        self.assertEqual(recheck_layout(image, layout, templates, DetectionConfig()), set())
        covered, _, _, _ = make_client(omit=('battle_list_title.png',))
        self.assertEqual(recheck_layout(covered, layout, templates, DetectionConfig()), {C.BATTLE_LIST})


FIXTURES = ['client_800x600', 'client_1920x1080', 'client_1920x1080_125', 'client_1920x1080_no_battle_list']


def fixture_paths(name):
    return f"tests/testdata/{name}.png", f"tests/testdata/{name}.expected.json"


def have_real_fixtures():
    files = [p for name in FIXTURES for p in fixture_paths(name)]
    templates = [os.path.join('images/ui', n) for n in DetectionConfig().template_files()]
    return all(os.path.isfile(p) for p in files + templates)


@unittest.skipUnless(have_real_fixtures(), 'real client fixtures and templates not captured yet (tasks T019-T021)')
class TestDetectRealFixtures(TestCase):
    """ T023: the same checks on captures of the official client """

    @classmethod
    def setUpClass(cls):
        cls.detector = TemplateDetector(DetectionConfig())

    def check_fixture(self, name):
        image_path, expected_path = fixture_paths(name)
        with open(expected_path, encoding='utf-8') as file:
            expected = json.load(file)
        layout = self.detector.detect(read_image(image_path))
        for component_type in C:
            wanted = expected[component_type.name]
            component = layout.get(component_type)
            self.assertEqual(component.found, wanted['found'], f"{name}: {component_type}")
            if wanted['found']:
                for actual, value in zip(component.region.as_list(), wanted['region']):
                    self.assertLessEqual(abs(actual - value), 3, f"{name}: {component_type}")
        return layout

    def test_fixtures(self):
        for name in FIXTURES:
            with self.subTest(name):
                layout = self.check_fixture(name)
                if name.endswith('no_battle_list'):
                    self.assertEqual(layout.get(C.BATTLE_LIST).missing_reason, 'anchor not found')

    def test_1920x1080_under_one_second(self):
        image = read_image(fixture_paths('client_1920x1080')[0])
        started = time.perf_counter()
        self.detector.detect(image)
        self.assertLess(time.perf_counter() - started, 1.0)

    def test_recheck_on_closed_battle_list(self):
        full = self.detector.detect(read_image(fixture_paths('client_1920x1080')[0]))
        closed = read_image(fixture_paths('client_1920x1080_no_battle_list')[0])
        self.assertIn(C.BATTLE_LIST, self.detector.recheck(closed, full))
