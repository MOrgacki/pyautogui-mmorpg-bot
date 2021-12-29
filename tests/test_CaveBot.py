from  unittest import IsolatedAsyncioTestCase
from PIL import Image
from modules.CaveBot import CaveBot

class TestCaveBot(IsolatedAsyncioTestCase):
    testing_instance = CaveBot()

    async def test_for_loot(self):
        loot_found_img = Image.open('tests/testdata/loot_found.png')

        result = await self.testing_instance.check_loot_area(loot_found_img)
        
        self.assertGreater(result[0].size, 0)
        self.assertGreater(result[1].size, 0)

    async def test_for_no_loot(self):
        loot_not_found_img = Image.open('tests/testdata/empty_loot.png')

        result = await self.testing_instance.check_loot_area(loot_not_found_img)
        
        self.assertEqual(result[0].size, 0)
        self.assertEqual(result[1].size, 0)