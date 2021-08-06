from multiprocessing import Value
import numpy as np
import pyautogui
import time
import sys
from PIL import *
from pebble import ProcessPool, concurrent
import keyboard
import jsonMaker


# https://stackoverflow.com/questions/54789250/q-terminate-a-process-called-in-a-function-from-another-function-in-python
# https://youtu.be/fKl2JW_qrso?t=583
# https://www.youtube.com/watch?v=CRJOQtaRT_8

# https://stackoverflow.com/questions/62111046/use-python-to-identify-elements-at-screen
# https://medium.com/@martin.lees/image-recognition-for-automation-with-python-711ac617b4e5


#     pyautogui.screenshot('chase.png', region=(1895, 190, 17, 17))

arrayPosition = 0


def InRange(number, number2):
    return number in range(1, 6)


@concurrent.process(name='setup')
def setUp():
    # pyautogui.click(pyautogui.locateCenterOnScreen(
    #     'images/utilities/minus.png'))
    # pyautogui.click(pyautogui.locateCenterOnScreen(
    #     'images/utilities/minus.png'))
    # pyautogui.click(pyautogui.locateCenterOnScreen(
    #     'images/utilities/minus.png'))
    # pyautogui.click(pyautogui.locateCenterOnScreen(
    #     'images/utilities/minus.png'))
    # pyautogui.click(pyautogui.locateCenterOnScreen(
    #     'images/utilities/plus.png'))
    pass


def doRandomPause(a, b):
    seconds = round(np.random.randint(a, b) / 1000, 2)
    time.sleep(seconds)


@concurrent.process(name='hunting')
def killandwalk():
    global arrayPosition
    while True:
        # if pyautogui.pixelMatchesColor(1725, 77, (0, 0, 0)) == True and pyautogui.pixelMatchesColor(1572, 61, (255, 0, 0)) == False:
        if pyautogui.pixel(1725, 77)[0] == 0 and pyautogui.pixel(1572, 61)[0] != 255:
            print('Attacking')
            pyautogui.hotkey('f1')
        elif pyautogui.pixel(1725, 77)[0] != 0:
            if arrayPosition < len(jsonMaker.json):
                print(f"walk {jsonMaker.json[arrayPosition]}")
                icon = pyautogui.locateCenterOnScreen(
                    jsonMaker.json[arrayPosition])
                pyautogui.click(icon)
                # Middle Point (x=1804, y=105)
                if icon == (1806, 104):
                    # if icon == (range(1803, 1806, 1), range(102, 106, 1)):
                    # pyautogui.click(icon)
                    arrayPosition += 1
            else:
                arrayPosition = 0
                icon = pyautogui.locateCenterOnScreen(
                    jsonMaker.json[arrayPosition])
                pyautogui.click(icon)
                arrayPosition += 1


@concurrent.process(name='chase')
def chase():
    while True:
        if pyautogui.locateCenterOnScreen('images/utilities/chase.png'):
            pyautogui.press('f2')
        print('chase')


@concurrent.process
def attackMode():
    while True:
        fullAtackIconPos = pyautogui.locateCenterOnScreen('fullAttack.png')
        pyautogui.click(fullAtackIconPos)
        return fullAtackIconPos


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
