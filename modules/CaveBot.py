import asyncio
import numpy as np
import random
import pyautogui
import time
from config.ImageProcessingConfig import ImageProcessingConfig

from config.PixelConfig import PixelConfig
from config.KeysConfig import KeysConfig
from helpers.Helpers import Helpers
from modules.AttackSpells import AttackSpells




class CaveBot():
    """ Main class which runs a cavebot """
    stopped = True
    going_to_wpt = False

    loot_points_list = [
        [221, 241],
        [187, 241],
        [190, 213],
        [193, 186],
        [221, 196],
        [248, 193],
        [253, 215],
        [257, 243],
        [221, 241],
    ]

    def __init__(self):
        #Load Pixels
        conf_pixel = PixelConfig()
        self._between = conf_pixel.get_between
        self._loot_boundary = conf_pixel.get_loot_boundary
        self._loot_color = conf_pixel.get_loot_color

        #Load Keys
        conf_keys = KeysConfig()
        self._attack_key = conf_keys.get_attack_key
        self._chase_key = conf_keys.get_chase_key

        #Load Areas
        conf_image = ImageProcessingConfig()
        self._battle_area = conf_image.get_battle_area
        self._chase_area = conf_image.get_chase_area
        self._chat_area = conf_image.get_chat_area
 

        #Battle List
        _battle_list = conf_pixel.get_battle_list
        _monster_red = conf_pixel.get_monster_red
        _chase = conf_pixel.get_chase
        
        self.check_for_monster = (_battle_list[0], _battle_list[1]) 
        self.check_for_combat = (_monster_red[0], _monster_red[1]) 
        self.check_for_chase = (_chase[0], _chase[1])

        #Attak Spells
        self._attack_spells = AttackSpells()


    async def check_loot_area(self, findings):
        """Check area for colour"""
        chat_area_array = np.array(findings)
        matches = np.where(np.all(chat_area_array == self._loot_color, axis=-1))
        print(matches)
        return matches
    

    async def attack_monster(self):
        """Attack monster"""
        self.going_to_wpt = False
        print('Monster Detected!')
        pyautogui.press(self._attack_key)
        Helpers.capture_area(self._battle_area)
        while True:
            monsters = Helpers.capture_area(self._battle_area)
            if  monsters.getpixel(self.check_for_combat)[0] == 255:
                await asyncio.sleep(0.01)
                print('Attacking!')
            else:
                break
        await asyncio.sleep(0.01) 
        

    async def walk_to_waypoint(self, loaded_json, arrayPos,going_to_wpt = False) -> None:
        """Waypoint walker"""
        if arrayPos < len(loaded_json):
            if going_to_wpt == False:
                going_to_wpt = True
                print(f"Walking to {loaded_json[arrayPos]}")
                icon = pyautogui.locateCenterOnScreen(
                loaded_json[arrayPos])
                pyautogui.click(icon)
                print('clicked map')
                x, y = icon
                while going_to_wpt:
                    icon = pyautogui.locateCenterOnScreen(
                    loaded_json[arrayPos])
                    x, y = icon
                    monsters = Helpers.capture_area(self._battle_area)
                    if monsters.getpixel(self.check_for_monster)[0] == 0 and monsters.getpixel(self.check_for_combat)[0] != 255:
                                break
                    if self._between[0][0] < x < self._between[0][1] and self._between[1][0] < y < self._between[1][1]:
                        arrayPos += 1
                        going_to_wpt = False
                    await asyncio.sleep(0.01) 
        else:
            arrayPos = 0
            going_to_wpt = False
        
        return arrayPos, going_to_wpt

    async def start_looting(self) -> None:
        """Performs looting"""

        random.shuffle(self.loot_points_list)
        pyautogui.keyDown('shift')
        for pos in self.loot_points_list:
            pyautogui.click(x=pos[0],y=pos[1], button='right')
            time.sleep(random.uniform(0.1,0.2))
        pyautogui.moveTo(221, 218)
        pyautogui.keyUp('shift')
        await asyncio.sleep(0.01)


    async def run_cvb(self, loaded_json) -> None:
        """Primary cavebot method"""
        arrayPos = 0

        while True:
            try:
                time.sleep(0.1)
                monsters = Helpers.capture_area(self._battle_area)
                # if theres is a monster not targeted
                if monsters.getpixel(self.check_for_monster)[0] == 0 and monsters.getpixel(self.check_for_combat)[0] != 255:
                    await asyncio.sleep(0.2)
                    # then attack monster
                    print('Monster Detected!')
                    await self.attack_monster()
                    # after that check loot area for a drop
                    matches = await self.check_loot_area(Helpers.capture_area(self._chat_area))
                    # if theres no monsters on screen then do looting
                    if matches[0].size > 0 and matches[1].size > 0:
                        await self.start_looting()
                # check if theres no monsters on screen
                elif Helpers.capture_area(self._battle_area).getpixel(self.check_for_monster)[0] != 0:
                    # then go to next waypoint
                    arrayPos, self.going_to_wpt = await self.walk_to_waypoint(loaded_json, arrayPos)
            except:
                # Refresh Map
                pyautogui.press('f6')
                print('Clicked F6 to refresh map')
