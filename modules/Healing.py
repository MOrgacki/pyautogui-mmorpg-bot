from config.ImageProcessingConfig import ImageProcessingConfig 

from config.KeysConfig import KeysConfig
from config.PixelConfig import PixelConfig


import asyncio

from helpers.Helpers import Helpers

class Healing():
    """ Class which executes healing """

    
    def __init__(self):
        #Load Pixels
        conf_pixel = PixelConfig()
        self._high_hp = conf_pixel.get_high_hp
        self._low_hp = conf_pixel.get_low_hp
        self._mana_bar = conf_pixel.get_mana_bar


        #Load Keys
        conf_keys = KeysConfig()
        self._high_hp_key = conf_keys.get_high_hp_key
        self._low_hp_key = conf_keys.get_low_hp_key
        self._mana_refill_key = conf_keys.get_mana_refill_key

        #Load Areas    
        conf_image = ImageProcessingConfig()
        self._heal_area = conf_image.get_heal_area



    async def primary_healing(self):
        """ Primary healing method """

        while True:
            refill_h_hp = Helpers.capture_area(self._heal_area).getpixel(self._high_hp)[0] != 255
            refill_l_hp = Helpers.capture_area(self._heal_area).getpixel(self._low_hp)[0] != 255
            refill_mana = Helpers.capture_area(self._heal_area).getpixel(self._mana_bar)[0] != 116

            if refill_l_hp:
                if refill_mana:
                     Helpers.press_key(self._mana_refill_key)
                else:
                     Helpers.press_key(self._low_hp_key)
                     print(self._low_hp_key)
            elif refill_h_hp and not refill_l_hp:
                if refill_mana:
                     Helpers.press_key(self._mana_refill_key)
                else:
                     Helpers.press_key(self._high_hp_key)
            elif refill_mana and not refill_h_hp and not refill_h_hp:
                Helpers.press_key(self._mana_refill_key)   
            await asyncio.sleep(0.01)
