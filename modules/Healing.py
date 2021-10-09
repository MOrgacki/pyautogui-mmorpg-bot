from PIL import ImageGrab
import time
import pyautogui

from config.KeysConfig import KeysConfig
from config.PixelConfig import PixelConfig


class Healing(KeysConfig, PixelConfig):

    def __init__(self):
        #Pixel loction attributes
        super(PixelConfig, self).__init__()
        # self._high_hp = high_hp
        # self._low_hp = low_hp
        # self._mana_bar = mana_bar

        #Wrapped with getters
        super(KeysConfig, self).__init__()
        # self._high_hp_key = high_hp_key
        # self._low_hp_key = low_hp_key
        # self._mana_refill_key = mana_refill_key

    """ High HP Getter """
    def get_high_hp(self):
        return self._high_hp_key

    """ Low HP Getter """
    def get_low_hp(self):
        return self._low_hp_key

    """ Mana Getter """
    def get_mana_refill(self):
        return self._mana_refill_key
    
    """ Realease key press to heal character """
    def press_key(key):
        pyautogui.press(key)
        print(key)
        time.sleep(.1)

    """ Primary healing method"""
    def primary_healing(self):
        while True:
            #bbox=(440, 0, 644, 110)
            condition_h_hp = ImageGrab.grab(
                bbox=(10, 0, 438, 20)).getpixel(self._high_hp)[0] == 31
            condition_l_hp = ImageGrab.grab(
                bbox=(10, 0, 438, 20)).getpixel(self._low_hp)[0] == 41
            condition_mana = ImageGrab.grab(
                bbox=(10, 0, 438, 20)).getpixel(self._mana_bar)[0] == 36

            if condition_l_hp:
                self.press_key(self.get_low_hp())
            elif condition_h_hp:
                if condition_mana:
                    self.press_key(self.get_mana_refill())
                else:
                    self.press_key(self.get_high_hp())
            else:
                print('Healing not needed')



