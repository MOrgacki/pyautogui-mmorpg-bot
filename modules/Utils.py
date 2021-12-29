import asyncio
import pyautogui
from config.ImageProcessingConfig import ImageProcessingConfig
from config.PixelConfig import PixelConfig
from config.KeysConfig import KeysConfig
import random
from helpers.Helpers import Helpers

class Utils:

    def __init__(self):
        """ Class includes all Utilities needed in game"""
        #Load Keys       
        conf_keys = KeysConfig()
        self._chase_key = conf_keys.get_chase_key
        self._food_key = conf_keys.get_food_key

         #Load Pixels   
        conf_pixel = PixelConfig()
        self._chase = conf_pixel.get_chase

        #Load Areas
        conf_image = ImageProcessingConfig()
        self._chase_area = conf_image.get_chase_area


    async def auto_chase(self):
        """ Auto chase """
        
        while True:
            if Helpers.capture_area(self._chase_area).getpixel((self._chase[0], self._chase[1]))[1] != 255:
                pyautogui.press(self._chase_key)
            else:
                await asyncio.sleep(round(random.uniform(1.05, 1.75), 2))

    async def auto_eat(self):
        """ Auto eating """
        
        while True:
            pyautogui.press(self._food_key)
            await asyncio.sleep(round(random.uniform(20.33, 30.66), 2))

        