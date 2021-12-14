import  unittest
from PIL import Image, ImageGrab
from modules.CaveBot import check_loot_area

class TestCaveBot(unittest.TestCase):

    def test_loot_area(self, findings):
        im = Image.open('/home/organ/Desktop/Fluffies/fluffies/tests/empty_loot.png')
        