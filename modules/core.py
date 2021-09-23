import numpy as np
import pyautogui
import time
from PIL import ImageGrab
from pebble import concurrent
import config as cfg
import keyboard


# https://stackoverflow.com/questions/54789250/q-terminate-a-process-called-in-a-function-from-another-function-in-python
# https://youtu.be/fKl2JW_qrso?t=583
# https://www.youtube.com/watch?v=CRJOQtaRT_8

# https://stackoverflow.com/questions/62111046/use-python-to-identify-elements-at-screen
# https://medium.com/@martin.lees/image-recognition-for-automation-with-python-711ac617b4e5


#     pyautogui.screenshot('chase.png', region=(1895, 190, 17, 17))


def doRandomPause(a, b):
    seconds = round(np.random.randint(a, b) / 1000, 2)
    time.sleep(seconds)


@concurrent.process(name='hunting')
def killandwalk(loaded_json):
    _arrayPos = 0
    while True:
        try:
            time.sleep(.3)
            # if R==0
            # bbox=(640,0, 744,110)
            battle_area = ImageGrab.grab(bbox=(440,0, 644,110))
            if battle_area.getpixel((cfg.battleListX, cfg.battleListY))[0] == 0 and battle_area.getpixel((cfg.monsterRedX, cfg.monsterRedY))[0] != 255:
                print('Rozpoznalem cel')
                pyautogui.press(cfg.attackKey)
                battle_area = ImageGrab.grab(bbox=(440,0, 644,110))
                while True:
                    battle_area = ImageGrab.grab(bbox=(440,0, 644,110))
                    if battle_area.getpixel((cfg.monsterRedX, cfg.monsterRedY))[0] == 255:
                    
                        print('Atakuje!')
                        time.sleep(2)
                        # if ImageGrab.grab().getpixel(cfg.looted)[0]  == 240 or ImageGrab.grab().getpixel(cfg.looted2)[0] == 240:
                    else:
                        break
                pyautogui.keyDown('shift')
                pyautogui.click(221, 241, button='right')
                time.sleep(.1)
                pyautogui.click(187, 241, button='right')
                time.sleep(.1)
                pyautogui.click(190, 213, button='right')
                time.sleep(.1)
                pyautogui.click(193, 186, button='right')
                time.sleep(.1)
                pyautogui.click(221, 196, button='right')
                time.sleep(.1)
                pyautogui.click(248, 193, button='right')
                time.sleep(.1)
                pyautogui.click(253, 215, button='right')
                time.sleep(.1)
                pyautogui.click(257, 243, button='right')
                time.sleep(.1)
                pyautogui.click(221, 241, button='right')
                time.sleep(.1)
                pyautogui.moveTo(221, 218)
                time.sleep(.1)
                pyautogui.keyUp('shift')
                time.sleep(.1)
                pyautogui.press('f4')
                time.sleep(.1)
                pyautogui.press('f5')
                time.sleep(.1)            
            # bbox=(440,0, 644,110)
            elif battle_area.getpixel((cfg.battleListX, cfg.battleListY))[0] != 0:
                # pos(x,y) must be around 1804,105 if so then char pyautogui.pixel(is in the middle of mark
                battle_area = ImageGrab.grab(bbox=(440,0, 644,110))
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

@concurrent.process(name='chase')
def chase():
    while True:

        """R==92 if chase is clcked."""
        if ImageGrab.grab().getpixel(cfg.chasePos)[0] != 92:
            pyautogui.press(cfg.chaseKey)
            print('chase')
        time.sleep(10)


@concurrent.process(name='heal')
def heal():

    while True:

        condition_h_hp = ImageGrab.grab().getpixel(cfg.high_hp)[0] == 40
        condition_l_hp = ImageGrab.grab().getpixel(cfg.low_hp)[0] == 34
        condition_mana = ImageGrab.grab().getpixel(cfg.mana_bar)[0] == 35
        # R==0 if heal is almost full
        if condition_h_hp and not condition_l_hp:
            if condition_mana:
                keyboard.press(cfg.mana_spell)
                print('ManaPotion UP')
                time.sleep(.1)
            else:
                keyboard.press(cfg.high_hp_spell)
                print('Weak Spell')
                time.sleep(.1)

        elif condition_l_hp:
            # else:
            keyboard.press(cfg.low_hp_spell)
            print('Strong Spell')
            time.sleep(.1)
