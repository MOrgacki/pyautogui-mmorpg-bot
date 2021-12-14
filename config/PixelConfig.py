

from config.Config import Config


class PixelConfig(Config):
    """Class contains bunch of getters to specific PIXEL location"""

    @property
    def get_attack(self):
        return self.get_property('attack')

    @property
    def get_chase(self):
        return self.get_property('chase')

    @property
    def get_battle_list(self):
        return self.get_property('battle_list')

    @property
    def get_monster_red(self):
        return self.get_property('monster_red')

    @property
    def get_between(self):
        return self.get_property('between')

    @property
    def get_high_hp(self):
        return self.get_property('high_hp')

    @property
    def get_low_hp(self):
        return self.get_property('low_hp')

    @property
    def get_mana_bar(self):
        return self.get_property('mana_bar')

    @property
    def get_loot_boundary(self):
        return self.get_property('loot_boundary')

    @property
    def get_battle_list_two_monsters(self):
        return self.get_property('battle_list_two_monsters')
    
    @property
    def get_battle_list_three_monsters(self):
        return self.get_property('battle_list_three_monsters')
