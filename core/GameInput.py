import asyncio
import random

import pyautogui


pyautogui.FAILSAFE = True
# Delays come from press_async/click_async, not from pyautogui's global pause
pyautogui.PAUSE = 0


class GameInput:
    """ Keyboard and mouse input that only reaches the client while it is the foreground window """

    def __init__(self, backend=pyautogui):
        self._backend = backend

    def _focused(self, window):
        return window is not None and window.refresh().is_foreground

    def press(self, window, key):
        """ Returns False and sends nothing when the client is not focused """
        if not self._focused(window):
            return False
        self._backend.press(key)
        return True

    def click(self, window, client_point, button='left', modifier=None):
        if not self._focused(window):
            return False
        x, y = window.to_screen(client_point)
        if modifier:
            self._backend.keyDown(modifier)
            try:
                self._backend.click(x=x, y=y, button=button)
            finally:
                self._backend.keyUp(modifier)
        else:
            self._backend.click(x=x, y=y, button=button)
        return True

    async def press_async(self, window, key):
        sent = self.press(window, key)
        if sent:
            await asyncio.sleep(random.uniform(0.1, 0.2))
        return sent

    async def click_async(self, window, client_point, button='left', modifier=None):
        sent = self.click(window, client_point, button, modifier)
        if sent:
            await asyncio.sleep(random.uniform(0.1, 0.2))
        return sent
