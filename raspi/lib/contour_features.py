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
    return area_scaled

def get_center(contour, roi_img):
    moments = cv2.moments(contour)
    try:
        cx = moments['m10']/moments['m00']
        cy = moments['m01']/moments['m00']
    except ZeroDivisionError:
        cx = 999
        cy = 999
        
    return cx / roi_img.shape[1], cy / roi_img.shape[0]

def get_area(contour, roi_img):
    area = cv2.contourArea(contour)
    roi_area = (roi_img.shape[0] * roi_img.shape[1])
    return area / roi_area 

def get_perimeter(contour, roi_img):
    perimeter = cv2.arcLength(contour, True)
    roi_perimeter = roi_img.shape[0]*2 + roi_img.shape[1]*2
    return perimeter / roi_perimeter

def get_point_count(contour, roi_img):
    return len(contour)

def get_orientation(contour, roi_img):
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