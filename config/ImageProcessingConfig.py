
from config.Config import Config


class ImageProcessingConfig(Config):
    """Class contains bunch of getters to specific IMAGE PROCESSING attributes"""
    
    @property
    def get_battle_area(self):
        return self.get_property('battle_area')

    @property
    def get_chase_area(self):
        return self.get_property('chase_area')

    @property
    def get_chat_area(self):
        return self.get_property('chat_area')

    @property
    def get_heal_area(self):
        return self.get_property('heal_area')
