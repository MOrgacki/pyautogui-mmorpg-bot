from PIL import ImageGrab
import pyautogui
import time
import numpy as np

from config.PixelConfig import PixelConfig
from config.KeysConfig import KeysConfig


class Utils:
    def __init__(self) -> None:
        conf_keys = KeysConfig()
        conf_pixel = PixelConfig()
        self._chase_key = conf_keys.get_chase_key
        self._chase = conf_pixel.get_chase

    def chase(self):
        while True:
            """R==92 if chase is clcked."""
            if ImageGrab.grab().getpixel(self._chase)[0] != 92:
                pyautogui.press(self._chase_key)
                print('chase')
            time.sleep(10)

    def do_random_pause(self, a, b):
        seconds = round(np.random.randint(a, b) / 1000, 2)
        time.sleep(seconds)
