
import numpy as np
import pyautogui
import time
from PIL import ImageGrab
from threading import Thread
import os

from config.PixelConfig import PixelConfig
from config.KeysConfig import KeysConfig


class CaveBot:
    # threading property
    stopped = True

    """ Class which runs a cavebot """
    def __init__(self):
        conf_pixel = PixelConfig()
        self._battle_list = conf_pixel.get_battle_list
        self._monster_red = conf_pixel.get_monster_red
        self._between = conf_pixel.get_between
        self._loot_boundary = conf_pixel.get_loot_boundary
        self._chase = conf_pixel.get_chase

        conf_keys = KeysConfig()
        self._attack_key = conf_keys.get_attack_key
        self._chase_key = conf_keys.get_chase_key


    """ Starts a thread """
    def start(self, loaded_json):
        self.stopped = False
        t = Thread(target=self.run_cvb, args=(loaded_json,))
        t.start()

    """ Stops a thread """
    def stop(self):
        self.stopped = True

    """Primary cavebot method"""
    def run_cvb(self, loaded_json):
        _arrayPos = 0
        while not self.stopped:
            try:
                time.sleep(.1)
                battle_area = ImageGrab.grab(bbox=(440, 0, 644, 110))
                # if theres is a monster not targeted
                if battle_area.getpixel((self._battle_list[0], self._battle_list[1]))[0] == 0 and battle_area.getpixel((self._monster_red[0], self._monster_red[1]))[0] != 255:
                    print('Monster Detected!')
                    pyautogui.press(self._attack_key)
                    battle_area = ImageGrab.grab(bbox=(440, 0, 644, 110))
                    while True:
                        battle_area = ImageGrab.grab(bbox=(440, 0, 644, 110))
                        if battle_area.getpixel((self._monster_red[0], self._monster_red[1]))[0] == 255:
                            print('Attacking!')
                            time.sleep(.1)
                            if ImageGrab.grab(bbox=(776, 150, 780, 158)).getpixel((self._chase[0], self._chase[1]))[1] != 255:
                                pyautogui.press(self._chase_key)
                                print('Activated Chase.')
                                time.sleep(.1)
                        else:
                            time.sleep(.1)
                            break
                    time.sleep(.1)
                    # check area for colour
                    chat_area = ImageGrab.grab(bbox=(0, 477, 60, 578))
                    chat_area_array = np.array(chat_area)
                    color = [240, 180, 0]
                    warunek = np.where(
                        np.all(chat_area_array == color, axis=-1))
                    print(warunek)
                    # if no monsters on screen then do looting
                    if warunek[0].size > 0 and warunek[1].size > 0:
                        time.sleep(.03)
                        pyautogui.keyDown('shift')
                        pyautogui.click(221, 241, button='right')
                        time.sleep(.03)
                        pyautogui.click(187, 241, button='right')
                        time.sleep(.03)
                        pyautogui.click(190, 213, button='right')
                        time.sleep(.05)
                        pyautogui.click(193, 186, button='right')
                        time.sleep(.03)
                        pyautogui.click(221, 196, button='right')
                        time.sleep(.03)
                        pyautogui.click(248, 193, button='right')
                        time.sleep(.03)
                        pyautogui.click(253, 215, button='right')
                        time.sleep(.03)
                        pyautogui.click(257, 243, button='right')
                        time.sleep(.03)
                        pyautogui.click(221, 241, button='right')
                        time.sleep(.03)
                        pyautogui.moveTo(221, 218)
                        time.sleep(.03)
                        pyautogui.keyUp('shift')
                        time.sleep(.3)
                # check if theres no monsters on screen
                elif battle_area.getpixel((self._battle_list[0], self._battle_list[1]))[0] != 0:
                    battle_area = ImageGrab.grab(bbox=(440, 0, 644, 110))
                    # go to next waypoint
                    if _arrayPos < len(loaded_json):
                        print(f"Walking to {loaded_json[_arrayPos]}")
                        icon = pyautogui.locateCenterOnScreen(
                            loaded_json[_arrayPos])
                        pyautogui.click(icon)
                        x, y = icon
                        print(self._between[0][0] < x < self._between[0][1]
                              and self._between[1][0] < y < self._between[1][1])
                        if self._between[0][0] < x < self._between[0][1] and self._between[1][0] < y < self._between[1][1]:
                            _arrayPos += 1
                    else:
                        _arrayPos = 0
            except:
                pyautogui.press('f6')
                print('Clicked F6 to refresh map')
