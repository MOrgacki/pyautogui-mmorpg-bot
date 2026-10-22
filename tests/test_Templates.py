import os
import tempfile
import unittest
from dataclasses import replace
from unittest import TestCase

import cv2
import numpy as np

from config.DetectionConfig import DetectionConfig
from detection.Templates import Templates


class TestTemplates(TestCase):

    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.config = replace(DetectionConfig(), templates_dir=self.dir.name)
        rng = np.random.default_rng(1)
        for name in self.config.template_files():
            cv2.imwrite(os.path.join(self.dir.name, name), rng.integers(0, 256, (20, 30, 3), dtype=np.uint8))

    def tearDown(self):
        self.dir.cleanup()

    def test_loads_every_template(self):
        templates = Templates(self.config)
        for name in self.config.template_files():
            self.assertEqual(templates.get(name).shape, (20, 30, 3))

    def test_missing_file_is_named(self):
        os.remove(os.path.join(self.dir.name, 'heart.png'))
        with self.assertRaises(FileNotFoundError) as caught:
            Templates(self.config)
        self.assertIn('heart.png', str(caught.exception))

    def test_scaled_variant(self):
        scaled = Templates(self.config).get('heart.png', 1.5)
        self.assertLessEqual(abs(scaled.shape[0] - 30), 1)
        self.assertLessEqual(abs(scaled.shape[1] - 45), 1)

    def test_load_mark(self):
        templates = Templates(self.config)
        mark = templates.load_mark('images/marks/checkmark.png')
        self.assertEqual(mark.ndim, 3)


@unittest.skipUnless(all(os.path.isfile(os.path.join('images/ui', n)) for n in DetectionConfig().template_files()),
                     'anchor templates not cropped yet (task T020)')
class TestRealTemplates(TestCase):

    def test_real_templates_load(self):
        Templates(DetectionConfig())
