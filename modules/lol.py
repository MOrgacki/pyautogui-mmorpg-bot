import cv2 as cv
import numpy as np

img = cv.imread('images/screen/screen2.png')


img = img[140:840, 350:1240]

lower = np.array([0, 63, 255])
upper = np.array([88, 255, 255])

hsv = cv.cvtColor(img, cv.COLOR_BGR2HSV)
mask = cv.inRange(hsv, lower, upper)
# output = cv.bitwise_and(img, img, mask=mask)

contours, hierarchy = cv.findContours(
    mask, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)
# red color (hMin = 26 , sMin = 139, vMin = 255), (hMax = 30 , sMax = 142, vMax = 255)

# for lower_blue in focus_area:
#     print(lower_blue)

cnt = contours[3]
# area = cv.contourArea(cnt)

x, y, w, h = cv.boundingRect(cnt)
cv.rectangle(img, (x, y), (x+w, y+h), (0, 255, 0), 2)

now = cv.drawContours(img, cnt, -1, (0, 255, 0), 3)
# contours, _ = cv.findContours(
#     mask_blue, cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE)
# res = cv.bitwise_and(focus_area, focus_area, mask=mask_blue)
# _, threshold = cv.threshold(
#     focus_area, thresh=254, maxval=255, type=cv.THRESH_BINARY)


cv.imshow("Contour s", now)
cv.waitKey(0)
