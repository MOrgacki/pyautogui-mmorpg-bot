from PIL import ImageGrab
import time
import pyautogui
from threading import Thread

from config.KeysConfig import KeysConfig
from config.PixelConfig import PixelConfig


class Healing():

    stopped = True
    
    """ Class which executes healing """
    def __init__(self):
        # Pixels
        conf_pixel = PixelConfig()
        self._high_hp = conf_pixel.get_high_hp
        self._low_hp = conf_pixel.get_low_hp
        self._mana_bar = conf_pixel.get_mana_bar


        # Keys
        conf_keys = KeysConfig()
        self._high_hp_key = conf_keys.get_high_hp_key
        self._low_hp_key = conf_keys.get_low_hp_key
        self._mana_refill_key = conf_keys.get_mana_refill_key


    """ Starts a thread """
    def start(self):
        self.stopped = False
        t = Thread(target=self.primary_healing)
        t.start()

    """ Stops a thread """
    def stop(self):
        self.stopped = True

    """ Realease key press to heal character """
    def press_key(self, key):
        pyautogui.press(key)
        print(key)
        time.sleep(.1)

    """ Primary healing method """
    def primary_healing(self):
        while not self.stopped:
            #bbox=(440, 0, 644, 110)
            condition_h_hp = ImageGrab.grab(
                bbox=(10, 0, 438, 20)).getpixel(self._high_hp)[0] == 31
            condition_l_hp = ImageGrab.grab(
                bbox=(10, 0, 438, 20)).getpixel(self._low_hp)[0] == 41
            condition_mana = ImageGrab.grab(
                bbox=(10, 0, 438, 20)).getpixel(self._mana_bar)[0] == 36

            if condition_l_hp:
                self.press_key(self._low_hp_key)
            elif condition_h_hp:
                if condition_mana:
                    self.press_key(self._mana_refill_key)
                else:
                    self.press_key(self._high_hp_key)
            else:
                print('Healing not needed')
