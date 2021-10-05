from PIL import ImageGrab
from pebble import concurrent
import config as cfg
import keyboard
import time
import pyautogui


@concurrent.process(name='heal')
def heal():

    while True:
        #bbox=(440, 0, 644, 110)
        condition_h_hp = ImageGrab.grab(
            bbox=(10, 0, 438, 20)).getpixel(cfg.high_hp)[0] == 31
        condition_l_hp = ImageGrab.grab(
            bbox=(10, 0, 438, 20)).getpixel(cfg.low_hp)[0] == 41
        condition_mana = ImageGrab.grab(
            bbox=(10, 0, 438, 20)).getpixel(cfg.mana_bar)[0] == 36
        if condition_l_hp:
            keyboard.press(cfg.low_hp_spell)
            print('Strong Spell')
            time.sleep(.1)
        elif condition_h_hp:
            if condition_mana:
                keyboard.press(cfg.mana_spell)
                print('ManaPotion UP')
                time.sleep(.1)
            else:
                keyboard.press(cfg.high_hp_spell)
                print('Weak Spell')
                time.sleep(.1)

        else:
            print('not supported')


@concurrent.process(name='random_heal')
def random_heal():
    pyautogui.press('f4')
    time.sleep(20)
