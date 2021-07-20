import cv2
import numpy as np
from PIL import ImageGrab
import pygetwindow as gw
import pyautogui
import time

# Attack TODO only 1 target


def attack():
    while True:
        if pyautogui.pixelMatchesColor(1748, 495, (63, 63, 63)):
            pyautogui.hotkey('.')


# Initialize screen


def initialize():
    # set chase
    pyautogui.screenshot('chase.png', region=(1895, 190, 17, 17))
    chaseIconPos = pyautogui.locateCenterOnScreen('chase.png')
    pyautogui.click(chaseIconPos)

    # set full atack
    pyautogui.screenshot('fullAttack.png', region=(1871, 166, 17, 17))
    fullAtackIconPos = pyautogui.locateCenterOnScreen('fullAttack.png')
    pyautogui.click(fullAtackIconPos)

    return chaseIconPos, fullAtackIconPos


# TODO


def healing():
    pyautogui.screenshot('chase.png', region=(1895, 190, 17, 17))
    chaseIconPos = pyautogui.locateCenterOnScreen('chase.png')
    return chaseIconPos


# Prepare
time.sleep(5)

if gw.isVisible('Tibia Tibia - Don Szpermix'):
    initialize()
    attack()

else:
    print('Brak okna')
