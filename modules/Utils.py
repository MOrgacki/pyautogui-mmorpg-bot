from PIL import ImageGrab
import pyautogui
import Config as cfg
import time
import numpy as np

class Utils:
    def __init__(self) -> None:
        pass

    def chase(self):
        while True:
            """R==92 if chase is clcked."""
            if ImageGrab.grab().getpixel(cfg.chasePos)[0] != 92:
                pyautogui.press(cfg.chaseKey)
                print('chase')
            time.sleep(10)

    def do_random_pause(self, a, b):
        seconds = round(np.random.randint(a, b) / 1000, 2)
        time.sleep(seconds)
