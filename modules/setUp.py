from pebble import concurrent
import pyautogui


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
        'images/utilities/plus.png'))


def attackMode():
    fullAtackIconPos = pyautogui.locateCenterOnScreen('fullAttack.png')
    pyautogui.click(fullAtackIconPos)
