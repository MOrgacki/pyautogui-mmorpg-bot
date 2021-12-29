from PIL import ImageGrab


battle_area = 645, 280, 740, 302
ss = ImageGrab.grab(bbox=battle_area)
ss.save('saved.png')