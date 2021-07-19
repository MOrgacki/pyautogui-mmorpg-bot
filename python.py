import cv2
import numpy as np
from PIL import ImageGrab
import pygetwindow
import pyautogui

# ImageGrab.grab = partial(ImageGrab.grab, all_screens=True)

# print('Press Ctrl-C to quit.')

# try:
#     while True:
#         x, y = pyautogui.position()
#         positionStr = 'X: ' + str(x).rjust(4) + ' Y: ' + str(y).rjust(4)
#         print(positionStr, end='')
#         print('\b' * len(positionStr), end='', flush=True)

# except KeyboardInterrupt:
#     print('\nDone.')


def chase():
    if pyautogui.locateOnWindow('uiControls/clickedChase.png', grayscale=True, confidence=.9):
        return
    else:
        cords = pyautogui.locateOnWindow(
            'uiControls/clickChase.png', grayscale=True, confidence=.9)
        pyautogui.click(cords[0], cords[1], 1)


titles = pygetwindow.getActiveWindow

while True:
    cars = pygetwindow.getActiveWindow()
    print(cars.left, cars.top, cars.width, cars.height)
    img = ImageGrab.grab(bbox=(int(cars.left),
                               int(cars.top),
                               int(cars.left + cars.width),
                               int(cars.top + cars.height)))
    frame = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
    pygetwindow.waitKey(1)
    pygetwindow.imshow('frame', frame)

if pygetwindow.isVisible('Tibia Tibia - Don Szpermix'):
    print('found title')
    chase()
else:
    print('Brak okna')
