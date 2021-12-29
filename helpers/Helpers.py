from PIL import ImageGrab
import pyautogui
import time
import random

class Helpers:

    @classmethod
    def capture_area(self, tuple):
        """ Makes a screen of a selected area """
        return ImageGrab.grab(bbox=tuple)
    
    @classmethod
    def press_key(self, key):
        """ Realease a key """
        pyautogui.hotkey(key)
        print("Pressed:" + key)
        time.sleep(random.uniform(0.1 , 0.2))    