# https://brokencode.io/how-to-easily-image-search-with-python/
from AppKit import NSScreen
print(
    f"Screen resolution is :{(NSScreen.mainScreen().frame().size.width, NSScreen.mainScreen().frame().size.height)}")


# https://stackoverflow.com/questions/53237266/how-can-i-minimize-maximize-windows-in-macos-with-the-cocoa-api-from-a-python-sc
# 1920x1080 screen size
# ??? window size

# pos config
healXpos, healYpos = 745, 55
chaseXpos, chaseYpos = 1902, 197

xPosBetween = 1808, 1803
yPosBetween = 106, 102

battleListX, battleListY = 1725, 77
monsterRedX, monsterRedY = 1572, 61


# keyboard config
attackKey = 'f1'
chaseKey = 'f2'
healingKey = 'f12'
