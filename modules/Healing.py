from PIL import ImageGrab
import pyautogui
import time 

from config.KeysConfig import KeysConfig
from config.PixelConfig import PixelConfig


import asyncio

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



    def start(self):
        """ Starts a module """
        self.stopped = False
        # t = Thread(target=self.primary_healing, name="Healing")
        # t.start()
        self.ThreadManager.NewThread(self.primary_healing)


    def stop(self):
        """ Stops a module """
        self.stopped = True


    def press_key(self, key):
        """ Realeases key press to heal character """
        pyautogui.hotkey(key)
        print(key)
        time.sleep(0.1)


    async def primary_healing(self):
        """ Primary healing method """
        print('started healing')
        self.stopped = False
        while not self.stopped:
            healing_area = ImageGrab.grab(
                bbox=(10, 0, 438, 20))
            condition_h_hp = healing_area.getpixel(self._high_hp)[0] == 31
            condition_l_hp = healing_area.getpixel(self._low_hp)[0] == 41
            condition_mana = healing_area.getpixel(self._mana_bar)[2] != 116

            if condition_l_hp:
                if condition_mana:
                     self.press_key(self._low_hp_key)
                else:
                     self.press_key(self._high_hp_key)
            elif condition_h_hp:
                if condition_mana:
                     self.press_key(self._mana_refill_key)
                else:
                     self.press_key(self._high_hp_key)
            elif condition_mana and not condition_l_hp and not condition_h_hp:
                self.press_key(self._mana_refill_key)   
            else:
                print('Healing not needed')
            await asyncio.sleep(0.01)
