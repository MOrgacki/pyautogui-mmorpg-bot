from PIL import ImageGrab
import pyautogui
import time
import random

class Helpers:

    @staticmethod
    def capture_area(tuple):
        """ Makes a screen of a selected area """
        return ImageGrab.grab(bbox=tuple)
    
    @staticmethod
    def press_key(key):
        """ Realease a key """
        pyautogui.hotkey(key)
        print("Pressed:" + key)
        time.sleep(random.uniform(0.1 , 0.2))    