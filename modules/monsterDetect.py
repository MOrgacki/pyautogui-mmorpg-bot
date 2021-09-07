# result_CCORR_NORMED = cv.matchTemplate(
#     screen_img, monster_img, cv.TM_CCORR_NORMED)
# result_TM_CCORR = cv.matchTemplate(screen_img, monster_img, cv.TM_CCORR)
# result_TM_SQDIFF = cv.matchTemplate(screen_img, monster_img, cv.TM_SQDIFF)
# result_TM_SQDIFF_NORMED = cv.matchTemplate(
#     screen_img, monster_img, cv.TM_SQDIFF_NORMED)

# result_TM_CCOEFF = cv.matchTemplate(screen_img, monster_img, cv.TM_CCOEFF)
# cv.imshow('result_CCORR_NORMED ', result_CCORR_NORMED)
# cv.imshow('result_TM_CCORR', result_TM_CCORR)
# cv.imshow('result_TM_SQDIFF', result_TM_SQDIFF)
# cv.imshow('result_TM_SQDIFF_NORMED', result_TM_SQDIFF_NORMED)
# cv.imshow('result_TM_CCOEFF', result_TM_CCOEFF)

import cv2 as cv
import numpy as np
from mss import mss


print(cv.imread('images/screen/monster.png',
                cv.IMREAD_COLOR).dtype)


monster_img = cv.imread(
    'images/screen/monster.png', cv.IMREAD_UNCHANGED)

screen_img = cv.imread(
    'images/screen/screen.png', cv.IMREAD_UNCHANGED)


'''
# The simplest use, save a screen shot of the 1st monitor
with mss() as sct:
    sct.shot()
'''


def pointMonster(background, matchImage, algoritm, threshold=0, monster_pos=[]):
    while True:
        result = cv.matchTemplate(
            background, matchImage, algoritm)

        _, maxVal, _, maxLoc = cv.minMaxLoc(result)
        print(f'Best match top left pos:{maxLoc}')
        print(f'Probability ratio {maxVal}')

        if maxVal >= threshold:
            print('Monster found and fits requirements')

            line_color = (0, 255, 0)
            lineType = cv.LINE_4
            line_thickness = 2

            monster_w = monster_img.shape[1]
            monster_h = monster_img.shape[0]

            top_left = maxLoc
            bottom_right = top_left[0] + monster_w, top_left[1] + monster_h

            cv.rectangle(screen_img, top_left, bottom_right,
                         line_color, line_thickness, lineType)

            center_x = top_left[0] + int(monster_w/2)
            center_y = top_left[1] + int(monster_h/2)
            monster_pos.append((center_y, center_y))
            cv.drawMarker(screen_img, (center_x, center_y),
                          line_color, cv.MARKER_CROSS)

            cv.imshow('resilt', screen_img)
            cv.waitKey()
        elif maxVal != 0 and maxVal < threshold:
            print('Monster doesnt fit requirements')
        else:
            print('Monster not found')
        return monster_pos


points = pointMonster(screen_img, monster_img,
                      cv.TM_CCOEFF_NORMED, threshold=0.1)
print(points)
