import json

class Waypoints:

    def __init__(self, name) -> None:
        self.name = name

    def select_json(self):
        file = open('./data/'+self.name,)

        loaded_json = json.load(file)
        loaded_json = loaded_json['waypoints']
        print(f"Initialized script with {len(loaded_json)} nodes")
        return loaded_json


# List of available icons

# 'images/marks/bagmark.png'
# 'images/marks/blueflagmark.png'
# 'images/marks/checkmark.png'
# 'images/marks/crossmark.png'
# 'images/marks/dollarmark.png'
# 'images/marks/exlamationmark.png'
# 'images/marks/knotdown.png'
# 'images/marks/knotup.png'
# 'images/marks/lipsmark.png'
# 'images/marks/lockermark.png'
# 'images/marks/pencilmark.png'
# 'images/marks/pointerdown.png'
# 'images/marks/pointerleft.png'
# 'images/marks/pointerright.png'
# 'images/marks/pointerup.png'
# 'images/marks/questionmark.png'
# 'images/marks/redcrossmark.png'
# 'images/marks/starkmark.png'
# 'images/marks/swordmark.png'