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


    """ Starts a thread """
    def start(self):
        self.stopped = False
        # t = Thread(target=self.primary_healing, name="Healing")
        # t.start()
        self.ThreadManager.NewThread(self.primary_healing)

    """ Stops a thread """
    def stop(self):
        self.stopped = True

    """ Realease key press to heal character """
    def press_key(self, key):
        pyautogui.hotkey(key)
        # keyboard.press_and_release('shift+f4')
        # self._keyboard.pre
        print(key)
        time.sleep(0.1)


    async def primary_healing(self):
        """ Primary healing method """
        self.stopped = False
        while not self.stopped:
            #bbox=(440, 0, 644, 110)
            healing_area = ImageGrab.grab(
                bbox=(10, 0, 438, 20))
            condition_h_hp = healing_area.getpixel(self._high_hp)[0] == 31
            condition_l_hp = healing_area.getpixel(self._low_hp)[0] == 41
            condition_mana = healing_area.getpixel(self._mana_bar)[0] == 36

            if condition_l_hp:
                 self.press_key(self._low_hp_key)
            elif condition_h_hp:
                if condition_mana:
                     self.press_key(self._mana_refill_key)
                else:
                     self.press_key(self._high_hp_key)
            else:
                print('Healing not needed')
            await asyncio.sleep(0.01)
