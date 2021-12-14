import asyncio
from PIL import ImageGrab
import pyautogui
from config.PixelConfig import PixelConfig
from config.KeysConfig import KeysConfig


class Utils:

    stopped = True
    lock = None

    def __init__(self):
        """ Class includes all Utilities needed in game"""
        conf_keys = KeysConfig()
        conf_pixel = PixelConfig()
        self._chase_key = conf_keys.get_chase_key
        self._chase = conf_pixel.get_chase
        self._food_key = conf_keys.get_food_key
    
    
    def start(self):
        """ Starts a thread """
        self.stopped = False
        # t = Thread(target=self.auto_eat, name="Utils")
        # t.start()


    def stop(self):
        """ Stops a thread """
        self.stopped = True


    async def chase(self):
        while True:
            """R==92 if chase is clcked."""
            if ImageGrab.grab().getpixel(self._chase)[0] != 92:
                pyautogui.press(self._chase_key)
                print('chase')
            await asyncio.sleep(30)

    # def do_random_pause(self, a, b):
    #     seconds = round(np.random.randint(a, b) / 1000, 2)
    #     time.sleep(seconds)

    async def auto_eat(self):
        print('started eating')
        self.stopped = False
        while self.stopped == False:
            # with Listener(on_press=key.key_press, on_release=key.key_release) as listener:
            #     listener.join()
            pyautogui.press(self._food_key)
            print('eating')
            await asyncio.sleep(30)


        