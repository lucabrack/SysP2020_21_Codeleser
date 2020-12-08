import cv2
import numpy as np
import math

## Enclosing Functions ##
# The following functions define, how the contours get enclosed

# Default
# nothing happens with the found contours
def contour(contours):
        return contours

# Ellipse Approximation
def approximation(contours):
    epsilon = 0.1*cv2.arcLength(contours,True)
    approx = cv2.approxPolyDP(contours,epsilon,True)
    return approx

# Convex Hull
def hull(contours):
    h = cv2.convexHull(contours)
    return h

# Bounding Rectangle
def rectangle(contours):
    x,y,w,h = cv2.boundingRect(contours)
    rect = np.array([[x,y],[x+w,y],[x+w,y+h],[x,y+h]])
    return rect

# Minimum Area Rectangle (Box)
def box(contours):
    min_rect = cv2.minAreaRect(contours)
    b = cv2.boxPoints(min_rect)
    b = np.int0(b)
    return b

# Minimum Enclosing Circle
def circle(contours):
    (x,y),radius = cv2.minEnclosingCircle(contours)
    center = (int(x),int(y))
    radius = int(radius)
    c = []
    # Create 50 points on circle periphery
    for a in np.linspace(0.0, 2*math.pi, num=50):
        x = center[0] + radius*math.cos(a)
        y = center[1] + radius*math.sin(a)
        c.append([x,y])
    c = np.array(c, dtype='int64')
    return c

# Replace contour with out of image points
# nothing gets drawn on frame
def none(contours):
    return np.array([[-1,-1]])

# Mask these function with simple key presses
enclosure_parser = {
    'c'    : contour,
    'a'    : approximation,
    'h'    : hull,
    'r'    : rectangle,
    'b'    : box,
    'k'    : circle,
    'n'    : none
}