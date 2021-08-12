import numpy as np
import pyautogui
import time
import sys
from PIL import *
from pebble import concurrent
import keyboard
import jsonMaker
from python_imagesearch.imagesearch import imagesearch, imagesearcharea, region_grabber
import config as cfg

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
def killandwalk():
    _arrayPos = 0
    while True:
        # if R==0
        if pyautogui.pixel(cfg.battleListX, cfg.battleListY)[0] == 0 and pyautogui.pixel(cfg.monsterRedX, cfg.monsterRedY)[0] != 255:
            print('Attacking')
            pyautogui.hotkey(cfg.attackKey)
        elif pyautogui.pixel(cfg.battleListX, cfg.battleListY)[0] != 0:
            # pos(x,y) must be around 1804,105 if so then char is in the middle of mark
            if _arrayPos < len(jsonMaker.json):
                print(f"Walking to {jsonMaker.json[_arrayPos]}")
                icon = pyautogui.locateCenterOnScreen(
                    jsonMaker.json[_arrayPos])
                # icon = imagesearcharea(
                #     jsonMaker.json[_arrayPos], 1752, 50, 1856, 157, precision=1.0)
                pyautogui.click(icon)
                x, y = icon
                # pos(x,y) must be around 1804,105
                if cfg.xPosBetween[0] > x > cfg.xPosBetween[1] and cfg.yPosBetween[0] > y > cfg.yPosBetween[1]:
                    _arrayPos += 1
            else:
                _arrayPos = 0


@concurrent.process(name='chase')
def chase():
    while True:
        """R==92 if chase is clcked."""
        if pyautogui.pixel(cfg.chaseXpos, cfg.chaseYpos)[0] != 92:
            pyautogui.press(cfg.chaseKey)
        print('chase')
        time.sleep(10)


@concurrent.process(name='heal')
def heal():
    while True:
        # R==0 if heal is almost full
        if pyautogui.pixel(cfg.healXpos, cfg.healYpos)[0] != 0:
            pyautogui.press(cfg.healingKey)
        print('chase')


# def stopProgram():
#     if keyboard.is_pressed('esc'):
#         sys.exit()

# def main():
#     time.sleep(5)
#     # with ProcessPool(max_workers=10) as pool:
#     #     # activateHunting(pool)
#     #     # activateChase(pool)
#     #     pass


# if __name__ == '__main__':
#     main()
#  if gw.isVisible('Tibia Tibia - Don Szpermix'):
# else:
#         print('Brak okna')
