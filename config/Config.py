
pixels = {
    'heal': (145, 9),
    'chase': (3, 6),

    'battle_list': (165, 32),
    'battle_list_two_monsters': (165, 54),
    'battle_list_three_monsters': (165, 75),
    'monster_red': (31, 23),

    'between': ((684, 690), (55, 70)),


    'high_hp': (77, 7),
    'low_hp': (43, 7),
    'mana_bar': (52, 20),

    'loot_boundary': ((51, 553), (51, 527)),
    'loot_color' : [240, 180, 0]

    }


keys = {
    'attack_key': 'f1',

    'chase_key': 'f12',

    'low_hp_key': 'f4',
    'high_hp_key': 'f8',
    'mana_refill_key':  'f7',
    
    'food_key':  'f5',
    
    'two_monsters_key': 'f2',
    'two_monsters_key_2': 'f3',
    'three_monsters_key': 'Del',
    'three_monsters_key_strong': 'End'
    }


image_processing = {

    'battle_area' : (440, 0, 644, 110),
    'chase_area' : (776, 150, 780, 158),
    'chat_area' : (0, 477, 60, 578),
    'heal_area' : (645, 280, 740, 302)
}



class Config:
    """Base Config Class"""

    def __init__(self) -> None:
        self._config_pixels = pixels
        self._config_keys = keys
        self._image_processing = image_processing

    def get_property(self, property_name):
        if property_name in self._config_pixels.keys():
            return self._config_pixels[property_name]
        elif property_name in self._config_keys.keys():
            return self._config_keys[property_name]
        elif property_name in self._image_processing.keys():
            return self._image_processing[property_name]             