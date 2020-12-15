import cv2
import numpy as np
import math

def get_center_roi(roi_attr, full_img):
    x,y,w,h = roi_attr
    cx = x + w/2
    cy = y + h/2
    return cx / full_img.shape[1], cy / full_img.shape[0]

def get_area_roi(roi_attr, full_img):
    x,y,w,h = roi_attr
    area = w*h
    area_scaled = area / (full_img.shape[0] * full_img.shape[1])
    return area, area_scaled

def get_center(contour, roi):
    moments = cv2.moments(contour)
    cx = moments['m10']/moments['m00']
    cy = moments['m01']/moments['m00']
    return cx / roi.shape[1], cy / roi.shape[0]

def get_area(contour, scale=1):
    area = cv2.contourArea(contour)
    return area / scale

def get_perimeter(contour, scale=1):
    perimeter = cv2.arcLength(contour, True)
    return perimeter / scale

def get_point_count(contour, scale=1):
    return len(contour)

def get_orientation(contour, scale=1):
    if len(contour) > 4:
        _, _, angle = cv2.fitEllipse(contour)
        return angle
    else:
        return 999


# Dict of these functions for easy loop through
feature_parser = {
    'c'    : get_center,
    'a'    : get_area,
    'p'    : get_perimeter,
    'l'    : get_point_count,
    'o'    : get_orientation
}