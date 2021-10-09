

class PixelConfig:

    """ Returns tuple of X,Y positions and position ranges """
    def __init__(self) -> None:
        self._heal = 145, 9
        self._chase = 3, 6

        self._battle_list = 165, 32
        self._monster_red = 31, 23

        self._between = (684, 690), (55, 70)


        self._high_hp = 180, 10
        self._low_hp = 67, 10
        self._mana_bar = 348, 10

        self._loot_boundary = (51, 553), (51, 527)