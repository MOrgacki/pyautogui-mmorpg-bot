import asyncio
import numpy as np

import pyautogui
from PIL import ImageGrab

from config.PixelConfig import PixelConfig
from config.KeysConfig import KeysConfig
from modules.AttackSpells import AttackSpells




class CaveBot():
    stopped = True

    # battle_area = (440, 0, 644, 110)
    # chase_area = (776, 150, 780, 158)
    # chat_area = (0, 477, 60, 578)

    battle_area = 440, 0, 644, 110
    chase_area = (776, 150, 780, 158)
    chat_area = (0, 477, 60, 578)
    loot_color = [240, 180, 0]

    """ Class which runs a cavebot """
    def __init__(self):
        conf_pixel = PixelConfig()
        self._between = conf_pixel.get_between
        self._loot_boundary = conf_pixel.get_loot_boundary
        

        conf_keys = KeysConfig()
        self._attack_key = conf_keys.get_attack_key
        self._chase_key = conf_keys.get_chase_key

     
        #Battle List
        _battle_list = conf_pixel.get_battle_list
        _monster_red = conf_pixel.get_monster_red
        _chase = conf_pixel.get_chase
        
        self.check_for_monster = (_battle_list[0], _battle_list[1]) 
        self.check_for_combat = (_monster_red[0], _monster_red[1]) 
        self.check_for_chase = (_chase[0], _chase[1])

        self._attack_spells = AttackSpells()
    
    """ Starts a thread """
    def start(self):
        self.stopped = False

    """ Stops a thread """
    def stop(self):
        self.stopped = True

    def capture_area(self, tuple):
        return ImageGrab.grab(bbox=tuple)

    # def pixel_of_area(self,x: Image, pixels, x_or_y: int):
    #     return x.getpixel(pixels)[x_or_y]
    
    async def check_loot_area(self):
            await asyncio.sleep(0.01)
            findings = self.capture_area(self.chat_area)
            chat_area_array = np.array(findings)
            matches = np.where(np.all(chat_area_array == self.loot_color, axis=-1))
            print(matches)
            return matches
    
    async def activate_chase(self):
        pyautogui.press(self._chase_key)
        print('Activated Chase.')
        await asyncio.sleep(0.1)

    async def attack_monter(self):
        print('Monster Detected!')
        pyautogui.press(self._attack_key)
        self.capture_area(self.battle_area)
        while True:
            self.capture_area(self.battle_area)
            if self.check_for_combat:
                print('Attacking!')
                await asyncio.sleep(0.1)
                if self.check_for_chase:
                    self.activate_chase()
                else:
                    break

    async def walk_to_waypoint(self, loaded_json, arrayPos) -> None:
         # go to next waypoint
        if arrayPos < len(loaded_json):
            print(f"Walking to {loaded_json[arrayPos]}")
            icon = pyautogui.locateCenterOnScreen(
            loaded_json[arrayPos])
            pyautogui.click(icon)
            # await asyncio.sleep(0.01)
            x, y = icon
            print(self._between[0][0] < x < self._between[0][1]
                and self._between[1][0] < y < self._between[1][1])
            if self._between[0][0] < x < self._between[0][1] and self._between[1][0] < y < self._between[1][1]:
                arrayPos += 1
        else:
            arrayPos = 0
        
        return arrayPos

    async def start_looting(self):
        # await asyncio.sleep(0.01)
        pyautogui.keyDown('shift')
        pyautogui.click(221, 241, button='right')
        pyautogui.click(187, 241, button='right')
        pyautogui.click(190, 213, button='right')
        pyautogui.click(193, 186, button='right')
        pyautogui.click(221, 196, button='right')
        pyautogui.click(248, 193, button='right')
        pyautogui.click(253, 215, button='right')
        pyautogui.click(257, 243, button='right')
        pyautogui.click(221, 241, button='right')
        pyautogui.moveTo(221, 218)
        pyautogui.keyUp('shift')

    async def run_cvb(self, loaded_json) -> None:

        
        """Primary cavebot method"""
        
        self.stopped = False
        # should_use_spells = False
        arrayPos = 0
        #TEST
        print('started walking')
        while not self.stopped:
            try:
                # await asyncio.sleep(0.01)
                monsters = self.capture_area(self.battle_area)
                chase = self.capture_area(self.chase_area)
                # if theres is a monster not targeted
                if monsters.getpixel(self.check_for_monster)[0] == 0 and monsters.getpixel(self.check_for_combat)[0] != 255:
                    await asyncio.sleep(0.2)
                    print('Monster Detected!')
                    pyautogui.press(self._attack_key)
                    monsters = self.capture_area(self.battle_area)
                    while True:
                        monsters = self.capture_area(self.battle_area)
                        if monsters.getpixel(self.check_for_combat)[0] == 255:
                            print('Attacking!')
                            # if should_use_spells == True:

                            #     self._attack_spells.run_spells()

                            await asyncio.sleep(0.1)
                            if chase.getpixel(self.check_for_chase)[1] != 255:
                                pyautogui.press(self._chase_key)
                                print('Activated Chase.')
                                await asyncio.sleep(0.1)
                        else:
                            break
                    # check loot area for colour
                    matches = await self.check_loot_area()
                    # if no monsters on screen then do looting
                    if matches[0].size > 0 and matches[1].size > 0:
                        await self.start_looting()
                        # x = self.capture_area(self.battle_area)
                # check if theres no monsters on screen
                elif self.capture_area(self.battle_area).getpixel(self.check_for_monster)[0] != 0:
                    x = self.capture_area(self.battle_area)
                    # go to next waypoint
                    arrayPos = await self.walk_to_waypoint(loaded_json, arrayPos)
            except:
                pyautogui.press('f6')
                print('Clicked F6 to refresh map')
