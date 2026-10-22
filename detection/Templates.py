import os

import cv2
import numpy as np


def read_image(path):
    """ Reads a PNG as a BGR array; raises FileNotFoundError naming the file """
    if not os.path.isfile(path):
        raise FileNotFoundError(path)
    data = np.fromfile(path, dtype=np.uint8)
    image = cv2.imdecode(data, cv2.IMREAD_COLOR)
    if image is None:
        raise FileNotFoundError(f"{path} is not a readable image")
    return image


def scale_image(image, scale):
    if scale == 1.0:
        return image
    height, width = image.shape[:2]
    size = (max(1, round(width * scale)), max(1, round(height * scale)))
    interpolation = cv2.INTER_AREA if scale < 1.0 else cv2.INTER_LINEAR
    return cv2.resize(image, size, interpolation=interpolation)


class Templates:
    """ Anchor and inner templates loaded once from images/ui/, with cached scaled copies """

    def __init__(self, config, images=None):
        """ images: optional {file name: BGR array}, used by tests instead of reading files """
        self._config = config
        if images is None:
            images = {name: read_image(os.path.join(config.templates_dir, name))
                      for name in config.template_files()}
        self._images = dict(images)
        self._scaled = {}

    def get(self, name, scale=1.0, gray=False):
        key = (name, round(scale, 3), gray)
        if key not in self._scaled:
            if name not in self._images:
                raise FileNotFoundError(name)
            image = scale_image(self._images[name], scale)
            self._scaled[key] = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if gray else image
        return self._scaled[key]

    def load_mark(self, path, scale=1.0):
        """ Waypoint mark from images/marks/, cached like the anchors """
        if path not in self._images:
            self._images[path] = read_image(path)
        return self.get(path, scale)

    def smallest_size(self):
        """ (width, height) of the smallest anchor at scale 1.0 """
        names = [n for files in self._config.anchor_templates.values() for n in files]
        sizes = [self._images[n].shape[1::-1] for n in names]
        return min(w for w, _ in sizes), min(h for _, h in sizes)
