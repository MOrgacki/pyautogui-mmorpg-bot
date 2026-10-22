import json
import os
import tempfile
from unittest import TestCase

from Waypoints import Waypoints, list_routes


class TestWaypoints(TestCase):

    def test_every_route_in_data_loads(self):
        for route in list_routes():
            with self.subTest(route.name):
                marks = Waypoints(route.name).select_json()
                self.assertIsInstance(marks, list)
                self.assertTrue(marks)

    def test_existing_routes_are_valid(self):
        self.assertTrue(all(r.valid for r in list_routes() if r.name == '3points.json'))

    def test_missing_mark_is_reported(self):
        with tempfile.TemporaryDirectory() as data_dir:
            with open(os.path.join(data_dir, 'broken.json'), 'w', encoding='utf-8') as file:
                json.dump({'waypoints': ['images/marks/bagmark.png', 'images/marks/nope.png']}, file)
            with open(os.path.join(data_dir, 'bad.json'), 'w', encoding='utf-8') as file:
                file.write('{')
            routes = {r.name: r for r in list_routes(data_dir)}
        self.assertFalse(routes['broken.json'].valid)
        self.assertEqual(routes['broken.json'].missing, ('images/marks/nope.png',))
        self.assertFalse(routes['bad.json'].valid)
        self.assertIsNotNone(routes['bad.json'].error)
