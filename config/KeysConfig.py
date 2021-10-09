

class KeysConfig:

    """ Returns strings contaiting config keys """
    def __init__(self) -> None:
        self._attack_key = 'f1'
        
        self._chase_key = 'f12'

        self._high_hp_key = 'f4'
        self._low_hp_key = 'f8'
        self._mana_refill_key = 'f7'

    def get_high_hp_key(self):
        return self._high_hp_key