import asyncio
from config.ImageProcessingConfig import ImageProcessingConfig

from config.PixelConfig import PixelConfig
from config.KeysConfig import KeysConfig
from helpers.Helpers import Helpers
import random

class AttackSpells:
    
    
    def __init__(self):
        
        #Load Keys
        conf_keys = KeysConfig()
        self.aoe_spell = conf_keys.get_three_monsters_key
        self.aoe_spell_2 = conf_keys.get_three_monsters_key_strong
        self.one_monster_spell = conf_keys.get_two_monsters_key
        self.one_monster_spell_2 = conf_keys.get_two_monsters_key_2
        
        #Load Pixels
        conf_pixel = PixelConfig()
        self.battle_list_two_monsters = conf_pixel.get_battle_list_two_monsters
        self.battle_list_three_monsters = conf_pixel.get_battle_list_three_monsters
        self.battle_list = conf_pixel.get_battle_list
        self._monster_red = conf_pixel.get_monster_red
        self.check_for_monster = (self.battle_list[0], self.battle_list[1]) 
        self.check_for_combat = (self._monster_red[0],self._monster_red[1]) 

        #Load Areas        
        conf_image = ImageProcessingConfig()
        self._battle_area = conf_image.get_battle_area

        
    async def run_spells(self):
        """ Primary attacking spells method """
        monsters = Helpers.capture_area(self._battle_area)

        while True:
            monsters = Helpers.capture_area(self._battle_area)

            if monsters.getpixel(self.battle_list)[0] == 0 and monsters.getpixel(self._monster_red)[0] == 255 and not monsters.getpixel(self.battle_list_three_monsters)[0] == 0:
                 Helpers.press_key(self.one_monster_spell)
                 Helpers.press_key(self.one_monster_spell_2)
                 monsters = Helpers.capture_area(self._battle_area)
                 await asyncio.sleep(random.uniform(2.3 , 2.8))
            elif monsters.getpixel(self.battle_list_three_monsters)[0] == 0 and monsters.getpixel(self._monster_red)[0] == 255:
                 Helpers.press_key(self.aoe_spell)
                 Helpers.press_key(self.aoe_spell_2)
                 monsters = Helpers.capture_area(self._battle_area)
                 await asyncio.sleep(random.uniform(2.3 , 2.8))
            else:
                print('Not attacking')
                await asyncio.sleep(0.01)
            