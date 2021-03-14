import os
import sys

import cv2
import math
import numpy as np

c_crop_rect = None

def add_pts(pt1, pt2):
    return tuple([x + y for x, y in zip(pt1, pt2)])

def round_pt(pt):
    return tuple([int(round(x)) for x in pt])

def plate_mask(image):
    # if c_crop_rect is None:
    #     mask = np.ones(image.shape, dtype=image.dtype) * 255
    # else:
    #     off = 10
    #     pt1 = round_pt(add_pts(c_crop_rect[0], (-off, -off)))
    #     pt2 = round_pt(add_pts(c_crop_rect[1], (off, off)))
    #     mask = np.zeros(image.shape, dtype=image.dtype)
    #     cv2.rectangle(mask, pt1, pt2, (255, 255, 255), -1)
    mask = np.ones(image.shape, dtype=image.dtype) * 255
    return mask

def magic(image,mask):
    gray = cv2.cvtColor(cv2.bitwise_and(mask, image), cv2.COLOR_BGR2GRAY)
    image /= 2
    image[cv2.bitwise_not(mask) == 255] /= 2


image = cv2.imread('holes.png',-1)
mask = plate_mask(image)
gray = cv2.cvtColor(cv2.bitwise_and(mask, image), cv2.COLOR_BGR2GRAY)
grayedge = cv2.Canny(gray,150,200)
edge = cv2.Canny(image,150,200)
#ret, thresh = cv2.threshold(grayedge, 127, 255, 0)
contours, hierarchy = cv2.findContours(grayedge, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)



#cv2.imshow("Holes",image)
#cv2.imshow("Edge",edge)
img = cv2.drawContours(grayedge, contours, -1, (255,255,255), 3)
cv2.imshow("Contours",img)








cv2.waitKey(0)
cv2.destroyAllWindows()