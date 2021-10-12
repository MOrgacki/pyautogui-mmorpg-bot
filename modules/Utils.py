from PIL import ImageGrab
import pyautogui
import time
import numpy as np
from threading import Thread
from config.PixelConfig import PixelConfig
from config.KeysConfig import KeysConfig


class Utils:

    stopped = True

    def __init__(self):
        conf_keys = KeysConfig()
        conf_pixel = PixelConfig()
        self._chase_key = conf_keys.get_chase_key
        self._chase = conf_pixel.get_chase
        self._food_key = conf_keys.get_food_key
    



    """ Starts a thread """
    def start(self):
        self.stopped = False
        t = Thread(target=self.auto_eat)
        t.start()

    """ Stops a thread """
    def stop(self):
        self.stopped = True


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

    def auto_eat(self):
        while self.stopped == False:
            pyautogui.press(self._food_key)
            print('eating')
            self.do_random_pause(9000,12000)