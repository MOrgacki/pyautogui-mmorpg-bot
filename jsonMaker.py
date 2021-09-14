import json
# 'bagmark': 'images/marks/bagmark.png',
# 'blueflagmark': 'images/marks/blueflagmark.png',
# 'checkmark': 'images/marks/checkmark.png',
# 'crossmark': 'images/marks/crossmark.png',
# 'dollarmark': 'images/marks/dollarmark.png',
# 'exlamationmark': 'images/marks/exlamationmark.png',
# 'knotdown': 'images/marks/knotdown.png',
# 'knotup': 'images/marks/knotup.png',
# 'lipsmark': 'images/marks/lipsmark.png',
# 'lockermark': 'images/marks/lockermark.png',
# 'pencilmark': 'images/marks/pencilmark.png',
# 'pointerdown': 'images/marks/pointerdown.png',
# 'pointerleft': 'images/marks/pointerleft.png',
# 'pointerright': 'images/marks/pointerright.png',
# 'pointerup': 'images/marks/pointerup.png',
# 'questionmark': 'images/marks/questionmark.png',
# 'redcrossmark': 'images/marks/redcrossmark.png',
# 'starkmark': 'images/marks/starkmark.png',
# 'swordmark': 'images/marks/swordmark.png'

file = open('waypoints.json',)

loaded_json = json.load(file)
loaded_json = loaded_json['waypoints']
print(f"Initialized script with {len(loaded_json)} nodes")
