from unittest import TestCase

import numpy as np

from detection.Components import ComponentType, DetectedComponent, Layout, Region


class TestRegion(TestCase):

    def test_rejects_empty_size(self):
        with self.assertRaises(ValueError):
            Region(0, 0, 0, 10)

    def test_contains(self):
        region = Region(10, 20, 30, 40)
        self.assertTrue(region.contains((10, 20)))
        self.assertTrue(region.contains((39, 59)))
        self.assertFalse(region.contains((40, 20)))
        self.assertFalse(region.contains((9, 30)))

    def test_crop(self):
        image = np.arange(100 * 100 * 3, dtype=np.uint32).reshape(100, 100, 3)
        crop = Region(10, 20, 30, 40).crop(image)
        self.assertEqual(crop.shape, (40, 30, 3))
        self.assertTrue((crop[0, 0] == image[20, 10]).all())

    def test_offset_and_center(self):
        region = Region(10, 20, 30, 40).offset(5, -5)
        self.assertEqual(region, Region(15, 15, 30, 40))
        self.assertEqual(region.center, (30, 35))


class TestLayout(TestCase):

    def make(self, found_types, game_view=Region(0, 0, 480, 352), tile_size=32):
        components = {}
        for t in ComponentType:
            if t in found_types:
                detail = {'tile_size': tile_size} if t is ComponentType.GAME_VIEW else {}
                region = game_view if t is ComponentType.GAME_VIEW else Region(0, 0, 10, 10)
                components[t] = DetectedComponent(t, True, region, 1.0, 1.0, detail)
            else:
                components[t] = DetectedComponent.missing(t, 'anchor not found')
        return Layout(1, (800, 600), components)

    def test_has(self):
        layout = self.make({ComponentType.HEALTH_BAR, ComponentType.MANA_BAR})
        self.assertTrue(layout.has(ComponentType.HEALTH_BAR))
        self.assertTrue(layout.has(ComponentType.HEALTH_BAR, ComponentType.MANA_BAR))
        self.assertFalse(layout.has(ComponentType.HEALTH_BAR, ComponentType.MINIMAP))
        self.assertEqual(layout.missing(ComponentType.MINIMAP, ComponentType.HEALTH_BAR), [ComponentType.MINIMAP])

    def test_tile_point_character_tile(self):
        layout = self.make({ComponentType.GAME_VIEW})
        # Character tile is column 7, row 5 -> centre (7.5 * 32, 5.5 * 32)
        self.assertEqual(layout.tile_point(0, 0), (240, 176))
        self.assertEqual(layout.tile_point(-1, 1), (208, 208))

    def test_tile_point_respects_game_view_position(self):
        layout = self.make({ComponentType.GAME_VIEW}, game_view=Region(100, 50, 480, 352))
        self.assertEqual(layout.tile_point(1, -1), (372, 194))

    def test_tile_point_needs_game_view(self):
        layout = self.make(set())
        with self.assertRaises(KeyError):
            layout.tile_point(0, 0)

    def test_empty_layout_has_every_type(self):
        layout = Layout.empty(1, (800, 600), 'window too small')
        self.assertEqual(set(layout.components), set(ComponentType))
        self.assertTrue(all(c.missing_reason == 'window too small' for c in layout.components.values()))
