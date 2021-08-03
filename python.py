from multiprocessing import Value
import numpy as np
import pyautogui
import time
import sys
from PIL import *
from pebble import ProcessPool
import keyboard
import jsonMaker

# initialize
# pyautogui.screenshot('chase.png', region=(1895, 190, 17, 17))
# pyautogui.screenshot('checkbox.png', region=(1791, 99, 5, 5))
# pyautogui.screenshot('star.png', region=(1767, 120, 5, 5))
# pyautogui.screenshot('fullAttack.png', region=(1871, 166, 17, 17))

# https://stackoverflow.com/questions/54789250/q-terminate-a-process-called-in-a-function-from-another-function-in-python
# https://youtu.be/fKl2JW_qrso?t=583
# https://www.youtube.com/watch?v=CRJOQtaRT_8

# https://stackoverflow.com/questions/62111046/use-python-to-identify-elements-at-screen
# https://medium.com/@martin.lees/image-recognition-for-automation-with-python-711ac617b4e5


#     pyautogui.screenshot('chase.png', region=(1895, 190, 17, 17))

arrayPosition = 0


def InRange(number, number2):
    return number in range(1, 6)


def setUp():
    pyautogui.click(pyautogui.locateCenterOnScreen(
        'images/utilities/minus.png'))
    pyautogui.click(pyautogui.locateCenterOnScreen(
        'images/utilities/minus.png'))
    pyautogui.click(pyautogui.locateCenterOnScreen(
        'images/utilities/minus.png'))
    pyautogui.click(pyautogui.locateCenterOnScreen(
        'images/utilities/minus.png'))
    pyautogui.click(pyautogui.locateCenterOnScreen(
        'images/utilities/minus.png'))
    pyautogui.click(pyautogui.locateCenterOnScreen(
        'images/utilities/minus.png'))
    pyautogui.click(pyautogui.locateCenterOnScreen(
        'images/utilities/minus.png'))
    pyautogui.click(pyautogui.locateCenterOnScreen(
        'images/utilities/plus.png'))


def doRandomPause(a, b):
    seconds = round(np.random.randint(a, b) / 1000, 2)
    time.sleep(seconds)


def killandwalk():
    global arrayPosition
    while True:
        # if pyautogui.pixelMatchesColor(1725, 77, (0, 0, 0)) == True and pyautogui.pixelMatchesColor(1572, 61, (255, 0, 0)) == False:
        if pyautogui.pixel(1725, 77)[0] == 0 and pyautogui.pixel(1572, 61)[0] != 255:
            print('attack')
            pyautogui.hotkey('f1')
            doRandomPause(500, 750)
        elif pyautogui.pixel(1725, 77)[0] != 0:
            if arrayPosition < len(jsonMaker.json):
                print(f"walk {jsonMaker.json[arrayPosition]}")
                icon = pyautogui.locateCenterOnScreen(
                    jsonMaker.json[arrayPosition])
                pyautogui.click(icon)
                doRandomPause(1000, 1450)
                # Middle Point (x=1804, y=105)
                if icon == (1806, 104):
                    # if icon == (range(1803, 1806, 1), range(102, 106, 1)):
                    pyautogui.click(icon)
                    arrayPosition += 1
            else:
                arrayPosition = 0
                icon = pyautogui.locateCenterOnScreen(
                    jsonMaker.json[arrayPosition])
                pyautogui.click(icon)
                arrayPosition += 1


def walk():
    while True:
        # if pyautogui.pixelMatchesColor(1725, 77, (0, 0, 0)) == False:
        #     starIcon = pyautogui.locateCenterOnScreen('star.png')
        #     pyautogui.click(starIcon)
        #     time.sleep(10)
        #     checkBoxIcon = pyautogui.locateCenterOnScreen('checkbox.png')
        #     pyautogui.click(checkBoxIcon)
        #     time.sleep(10)
        print('walk')
        time.sleep(3)


def kill():
    while True:
        # if pyautogui.pixelMatchesColor(1725, 77, (0, 0, 0)) == True and pyautogui.pixelMatchesColor(1572, 61, (255, 0, 0)) == False:
        #     global iskilling
        #     iskilling = True
        #     pyautogui.hotkey('f1')
        #     time.sleep(1)
        print('kill')
        time.sleep(3)


def chase():
    while True:
        if pyautogui.locateCenterOnScreen('images/utilities/chase.png'):
            pyautogui.press('f2')
        print('chase')


def attackMode():
    while True:
        fullAtackIconPos = pyautogui.locateCenterOnScreen('fullAttack.png')
        pyautogui.click(fullAtackIconPos)
        return fullAtackIconPos

# EXIT


# def stopProgram():
#     if keyboard.is_pressed('esc'):
#         sys.exit()


if __name__ == '__main__':
    time.sleep(5)
    # setUp()

    with ProcessPool() as pool:
        p1 = pool.schedule(killandwalk)
        p2 = pool.schedule(chase)


#  if gw.isVisible('Tibia Tibia - Don Szpermix'):
# else:
#         print('Brak okna')
