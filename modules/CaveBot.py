import numpy as np
import pyautogui
import time
from PIL import ImageGrab
from threading import Thread

class CaveBot:
    pass
    # #threading properties
    # stopped = True

    # def __init__(self):
    #     pass

    # def start(self, selected_name):
    #     self.stopped = False
    #     t = Thread(target=self.run_cvb,args=selected_name)
    #     t.start()

    # def stop(self):
    #     self.stopped = True

    # def run_cvb(self, loaded_json):
    #     _arrayPos = 0
    #     while not self.stopped:
    #         try:
    #             time.sleep(.1)
    #             battle_area = ImageGrab.grab(bbox=(440, 0, 644, 110))
    #             #if theres is a monster not targeted
    #             if battle_area.getpixel((Config.battleListX, Config.battleListY))[0] == 0 and battle_area.getpixel((Config.monsterRedX, Config.monsterRedY))[0] != 255:
    #                 print('Monster Detected!')
    #                 pyautogui.press(Config.attackKey)
    #                 battle_area = ImageGrab.grab(bbox=(440, 0, 644, 110))
    #                 while True:
    #                     battle_area = ImageGrab.grab(bbox=(440, 0, 644, 110))
    #                     if battle_area.getpixel((Config.monsterRedX, Config.monsterRedY))[0] == 255:
    #                         print('Attacking!')
    #                         time.sleep(.1)
    #                         if ImageGrab.grab(bbox=(776, 150, 780, 158)).getpixel((Config.chasePosX, Config.chasePosY))[1] != 255:
    #                             pyautogui.press(Config.chaseKey)
    #                             print('Activated Chase.')
    #                             time.sleep(.1)
    #                     else:
    #                         time.sleep(.1)
    #                         break
    #                 time.sleep(.1)
    #                 #check area for colour
    #                 chat_area = ImageGrab.grab(bbox=(0, 477, 60, 578))
    #                 chat_area_array = np.array(chat_area)
    #                 color = [240, 180, 0]
    #                 warunek = np.where(np.all(chat_area_array == color, axis=-1))
    #                 print(warunek)
    #                 #if no monsters on screen then do looting
    #                 if warunek[0].size > 0 and warunek[1].size > 0:
    #                     time.sleep(.03)
    #                     pyautogui.keyDown('shift')
    #                     pyautogui.click(221, 241, button='right')
    #                     time.sleep(.03)
    #                     pyautogui.click(187, 241, button='right')
    #                     time.sleep(.03)
    #                     pyautogui.click(190, 213, button='right')
    #                     time.sleep(.05)
    #                     pyautogui.click(193, 186, button='right')
    #                     time.sleep(.03)
    #                     pyautogui.click(221, 196, button='right')
    #                     time.sleep(.03)
    #                     pyautogui.click(248, 193, button='right')
    #                     time.sleep(.03)
    #                     pyautogui.click(253, 215, button='right')
    #                     time.sleep(.03)
    #                     pyautogui.click(257, 243, button='right')
    #                     time.sleep(.03)
    #                     pyautogui.click(221, 241, button='right')
    #                     time.sleep(.03)
    #                     pyautogui.moveTo(221, 218)
    #                     time.sleep(.03)
    #                     pyautogui.keyUp('shift')
    #                     time.sleep(.3)
    #             #check if theres no monsters on screen
    #             elif battle_area.getpixel((Config.battleListX, Config.battleListY))[0] != 0:
    #                 battle_area = ImageGrab.grab(bbox=(440, 0, 644, 110))
    #                 #go to next waypoint
    #                 if _arrayPos < len(loaded_json):
    #                     print(f"Walking to {loaded_json[_arrayPos]}")
    #                     icon = pyautogui.locateCenterOnScreen(
    #                         loaded_json[_arrayPos])
    #                     pyautogui.click(icon)
    #                     x, y = icon
    #                     print(Config.xPosBetween[0] > x > Config.xPosBetween[1]
    #                         and Config.yPosBetween[0] > y > Config.yPosBetween[1])
    #                     if Config.xPosBetween[0] < x < Config.xPosBetween[1] and Config.yPosBetween[0] < y < Config.yPosBetween[1]:
    #                         _arrayPos += 1
    #                 else:
    #                     _arrayPos = 0
    #         except:
    #             pyautogui.press('f6')
    #             print('Clicked F6 to refresh map')
