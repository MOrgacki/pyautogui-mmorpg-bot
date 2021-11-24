from PIL import ImageGrab


battle_area = 440, 0, 644, 110
ss = ImageGrab.grab(bbox=battle_area)
ss.save('saved.png')