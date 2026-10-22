import cv2
import dearpygui.dearpygui as dpg
import numpy as np


OUTLINE = (80, 220, 120, 255)
LABEL = (255, 255, 255, 255)


def fit(size, box):
    """ Scale factor that fits size (w, h) inside box (w, h) """
    return min(box[0] / size[0], box[1] / size[1])


def to_texture(image, width, height):
    """ BGR capture -> flat RGBA float32 data for a width x height texture, letterboxed """
    scale = fit(image.shape[1::-1], (width, height))
    resized = cv2.resize(image, (max(1, int(image.shape[1] * scale)), max(1, int(image.shape[0] * scale))),
                         interpolation=cv2.INTER_AREA)
    canvas = np.zeros((height, width, 4), np.float32)
    canvas[..., 3] = 1.0
    h, w = resized.shape[:2]
    canvas[:h, :w, :3] = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB) / 255.0
    return canvas.ravel(), scale


class DetectionPreview:
    """ Latest client capture with an outline and label per found component """

    def __init__(self, width=396, height=270):
        self.width = width
        self.height = height
        self._shown_generation = None
        with dpg.texture_registry():
            self._texture = dpg.add_dynamic_texture(width, height, [0.0] * (width * height * 4))
        self._drawlist = None

    def build(self, parent):
        self._drawlist = dpg.add_drawlist(self.width, self.height, parent=parent)
        dpg.draw_text((8, 8), 'No detection yet', color=LABEL, size=14, parent=self._drawlist)

    def update(self, layout, capture, force=False):
        """ Redraws when the layout generation changes (or when forced) """
        if layout is None or capture is None:
            return
        if not force and layout.generation == self._shown_generation:
            return
        self._shown_generation = layout.generation
        data, scale = to_texture(capture, self.width, self.height)
        dpg.set_value(self._texture, data)
        dpg.delete_item(self._drawlist, children_only=True)
        dpg.draw_image(self._texture, (0, 0), (self.width, self.height), parent=self._drawlist)
        for component_type, component in layout.components.items():
            if not component.found:
                continue
            region = component.region
            top_left = (region.x * scale, region.y * scale)
            bottom_right = ((region.x + region.width) * scale, (region.y + region.height) * scale)
            dpg.draw_rectangle(top_left, bottom_right, color=OUTLINE, thickness=1, parent=self._drawlist)
            dpg.draw_text((top_left[0], max(0, top_left[1] - 12)), component_type.value,
                          color=LABEL, size=11, parent=self._drawlist)
