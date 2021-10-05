import numpy as np
import pyautogui
import time
from PIL import ImageGrab
from pebble import concurrent
import config as cfg


def doRandomPause(a, b):
    seconds = round(np.random.randint(a, b) / 1000, 2)
    time.sleep(seconds)


@concurrent.process(name='hunting')
def killandwalk(loaded_json):
    _arrayPos = 0
    while True:
        try:
            time.sleep(.1)
            battle_area = ImageGrab.grab(bbox=(440, 0, 644, 110))
            if battle_area.getpixel((cfg.battleListX, cfg.battleListY))[0] == 0 and battle_area.getpixel((cfg.monsterRedX, cfg.monsterRedY))[0] != 255:
                print('Rozpoznalem cel')
                pyautogui.press(cfg.attackKey)
                battle_area = ImageGrab.grab(bbox=(440, 0, 644, 110))
                while True:
                    battle_area = ImageGrab.grab(bbox=(440, 0, 644, 110))
                    if battle_area.getpixel((cfg.monsterRedX, cfg.monsterRedY))[0] == 255:
                        print('Atakuje!')
                        time.sleep(.1)
                        if ImageGrab.grab(bbox=(776, 150, 780, 158)).getpixel((cfg.chasePosX, cfg.chasePosY))[1] != 255:
                            pyautogui.press(cfg.chaseKey)
                            print('chase')
                            time.sleep(.1)
                    else:
                        time.sleep(.1)
                        break
                time.sleep(.1)
                chat_area = ImageGrab.grab(bbox=(0, 477, 60, 578))
                chat_area_array = np.array(chat_area)
                color = [240, 180, 0]
                warunek = np.where(np.all(chat_area_array == color, axis=-1))
                print(warunek)
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
            elif battle_area.getpixel((cfg.battleListX, cfg.battleListY))[0] != 0:
                battle_area = ImageGrab.grab(bbox=(440, 0, 644, 110))
                if _arrayPos < len(loaded_json):
                    print(f"Walking to {loaded_json[_arrayPos]}")
                    icon = pyautogui.locateCenterOnScreen(
                        loaded_json[_arrayPos])
                    pyautogui.click(icon)
                    x, y = icon
                    print(cfg.xPosBetween[0] > x > cfg.xPosBetween[1]
                          and cfg.yPosBetween[0] > y > cfg.yPosBetween[1])
                    if cfg.xPosBetween[0] < x < cfg.xPosBetween[1] and cfg.yPosBetween[0] < y < cfg.yPosBetween[1]:
                        _arrayPos += 1
                else:
                    _arrayPos = 0
        except:
            pyautogui.press('f6')
            print('Clicked f6')


@ concurrent.process(name='chase')
def chase():
    while True:

        """R==92 if chase is clcked."""
        if ImageGrab.grab().getpixel(cfg.chasePos)[0] != 92:
            pyautogui.press(cfg.chaseKey)
            print('chase')
        time.sleep(10)
