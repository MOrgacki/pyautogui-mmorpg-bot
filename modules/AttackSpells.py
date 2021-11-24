import asyncio
import numpy as np
import time

import pyautogui
from PIL import ImageGrab

from config.PixelConfig import PixelConfig
from config.KeysConfig import KeysConfig

class AttackSpells:
    battle_area = 440, 0, 644, 110
    
    def __init__(self) -> None:

        conf_keys = KeysConfig()
        self.aoe_spell = conf_keys.get_three_monsters_key
        self.one_monster_spell = conf_keys.get_two_monsters_key
        self.one_monster_spell_2 = conf_keys.get_two_monsters_key_2
        
        conf_pixel = PixelConfig()
        self.battle_list_two_monsters = conf_pixel.get_battle_list_two_monsters
        self.battle_list_three_monsters = conf_pixel.get_battle_list_three_monsters
        self.battle_list = conf_pixel.get_battle_list
        self._monster_red = conf_pixel.get_monster_red
        self.check_for_monster = (self.battle_list[0], self.battle_list[1]) 
        self.check_for_combat = (self._monster_red[0],self._monster_red[1]) 
    def start(args):
        pass

    def stop(args):
        pass

    """ Realease key press to heal character """
    def press_key(self, key):
        pyautogui.hotkey(key)
        # keyboard.press_and_release('shift+f4')
        # self._keyboard.pre
        print(key)
        time.sleep(0.1)

    def capture_area(self, tuple):
        return ImageGrab.grab(bbox=tuple)

    async def run_spells(self):
        """ Primary healing method """
        self.stopped = False
        monsters = self.capture_area(self.battle_area)

        # battle_list = monsters.getpixel(self.battle_list)[0] == 0
        # combat = monsters.getpixel(self._monster_red)[0] == 255
        # battle_list_two_monsters = monsters.getpixel(self.battle_list_two_monsters)[0] == 0
        # battle_list_three_monsters = monsters.getpixel(self.battle_list_three_monsters)[0] == 0

        while not self.stopped:
            #bbox=(440, 0, 644, 110)
            monsters = self.capture_area(self.battle_area)
            if monsters.getpixel(self.battle_list)[0] == 0 and monsters.getpixel(self._monster_red)[0] == 255 and not monsters.getpixel(self.battle_list_three_monsters)[0] == 0:
                 self.press_key(self.one_monster_spell)
                 self.press_key(self.one_monster_spell_2)
                 monsters = self.capture_area(self.battle_area)
                 await asyncio.sleep(2.5)
            elif monsters.getpixel(self.battle_list_three_monsters)[0] == 0 and monsters.getpixel(self._monster_red)[0] == 255:
                 self.press_key(self.aoe_spell)
                 monsters = self.capture_area(self.battle_area)
                 await asyncio.sleep(2.5)
            else:
                print('Not attacking')
                await asyncio.sleep(0.01)
            