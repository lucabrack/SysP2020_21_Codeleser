# import image processing libraries
import cv2
import numpy as np
import math

from lib.enclosings import *
from lib.contour_features import *

#clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(4,4))

# Convert image to grayscale
def grayscale(img):
    return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

# Convert image to BGR-Colorspace
def bgr(img):
    return cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)

# Scale the thresholding block with the size of the Image
def scale_block(img, param):
    val = int(param)
    val_pix = int(img.shape[1] * val / 100)
    if val_pix <= 1:
        return 3
    elif val_pix % 2 == 1:
        return val_pix
    else:
        return val_pix + 1

# Scale the blurring block with the size of the Image
def scale_blur(img, param):
    val = int(param) / 10 # reduce to 10% of the image size
    val_pix = int(img.shape[1] * val / 100)
    if val_pix > 15:
        return 15
    elif val_pix % 2 == 1:
        return val_pix
    else:
        return val_pix + 1

# Find and return coordinates from Region Of Interest (ROI)
def get_roi_attr(img_gray, image_parameters):
    # Define all parameters from config file
    BLUR_FULL = scale_blur(img_gray, image_parameters['blur_full'])
    THRESH_BLOCK_FULL = scale_block(img_gray, image_parameters['thresh_block_full'])
    THRESH_CONST_FULL = int(image_parameters['thresh_const_full'])

    # blur the image to filter out unwanted noise
    # blur is deactivated for now (it's too computationally intensive)
    #blur = cv2.medianBlur(img_gray,BLUR_FULL)
    blur = img_gray

    # Adaptive thresholding to get a black and white image
    thresh = cv2.adaptiveThreshold(blur,255,cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY_INV,THRESH_BLOCK_FULL,THRESH_CONST_FULL)

    # use floodfill to fill all the small holes and infill our border rectangles white
    fill = thresh.copy()
    h, w = fill.shape[:2]
    mask = np.zeros((h+2,w+2), np.uint8)
    cv2.floodFill(fill, mask, (0,0), 255)
    fill_inv = cv2.bitwise_not(fill)
    img_thresh = thresh | fill_inv

    # find all contours on the full image and hopefully also the border rectangles
    cont, _ = cv2.findContours(img_thresh, 1, 2)
      
    # Check if any contours were found
    if len(cont) > 0:
        c = max(cont, key = cv2.contourArea) # find contour with biggest Area
        attr = cv2.boundingRect(c) # Enclose the biggest contour with a rectangle
    else: # No contours found
        attr = None
    
    return attr, img_thresh

# Get Region of Interest (ROI)
def get_roi(img, roi_attr):
    # cut the roi out of the image
    # use only 90% of the image to leave out the border
    x,y,w,h = roi_attr
    offset_ratio = 0.1
    offset_x= int(offset_ratio*w)
    offset_y= int(offset_ratio*h)
    return img.copy()[y+offset_y:y+h-offset_y,x+offset_x:x+w-offset_x]

# Get all contours in the Region Of Interest (ROI)
def get_roi_contours(roi_gray, image_parameters):
    # Define all parameters from config file
    BLUR_ROI = scale_blur(roi_gray, image_parameters['blur_roi'])
    THRESH_BLOCK_ROI = scale_block(roi_gray, image_parameters['thresh_block_roi'])
    THRESH_CONST_ROI = int(image_parameters['thresh_const_roi'])

    # blur the image to filter out unwanted noise
    # blur is deactivated for now (it's too computationally intensive)
    #roi_blur = cv2.medianBlur(roi_gray,BLUR_ROI)
    roi_blur = roi_gray

    # TEST: use adaptive histogram matching to better the contrast on the image
    #roi_clahe = clahe.apply(roi_blur)

    # sharpen image
    blur = cv2.GaussianBlur(roi_blur, (0,0), 3)
    roi_sharpen = cv2.addWeighted(roi_blur, 1.5, blur, -0.5, 0)

    # Adaptive thresholding to get a black and white image
    roi_thresh = cv2.adaptiveThreshold(roi_sharpen,255,cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY_INV,THRESH_BLOCK_ROI,THRESH_CONST_ROI)
    # find the contours on the zoom image
    cont_roi, _ = cv2.findContours(roi_thresh, 1, 2)

    roi_area = roi_gray.shape[0] * roi_gray.shape[1]
    contour_threshold = 1 / 3000

    # Only accept Contours that have a minimum area
    cont = []
    for c in cont_roi:
        if c.size > 4: # more than 2 points have to be found (2 coorinates per point -> 2 points * 2 coordinates = size 4)
            area_ratio = cv2.contourArea(c) / roi_area # relative area to make it independent of image size
            if area_ratio > contour_threshold:
                cont.append(c)
    
    return cont, roi_thresh


def get_shapes(contours, roi):
    shapes = []

    enclosing_circles = [ circle(x) for x in contours ]
    circle_areas = [ get_area(x, roi) for x in enclosing_circles ]
    circle_median_area = np.median(circle_areas)

    def in_range(input_value, base_value, percent):
        return (1-percent)*base_value <= input_value <= (1+percent)*base_value

    shape_area_range = 0.20
    for contour, circle_area in zip(contours, circle_areas):
        # Check if the contour is roughly the right size
        if circle_median_area * 0.5 <= circle_area <= circle_median_area * 3:
            # Check if the shape is a circle
            contour_area = get_area(contour, roi)
            if in_range(contour_area/circle_area, 1, shape_area_range):
                shapes.append([0, get_center(contour, roi)])
            
            else: # not a circle
                # Check if the shape is a rectangle
                enclosing_rectangle = rectangle(contour)
                rectangle_area = get_area(enclosing_rectangle, roi)
                if in_range(contour_area/rectangle_area, 1, shape_area_range):
                    shapes.append([2, get_center(contour, roi)])
                
                else: # not a rectangle
                    # Check if the shape is a triangle
                    enclosing_hull = hull(contour)
                    hull_area = get_area(enclosing_hull, roi)
                    if in_range(contour_area/hull_area, 1, shape_area_range):
                        shapes.append([1, get_center(contour, roi)])
                    
                    else: # not a triangle
                        # so it must be a cross
                        shapes.append([3, get_center(contour, roi)])
    
    return shapes

            

# Draw all the contours given in a list
def draw_contours(img, contours):
    cv2.drawContours(img, contours, -1, (255,0,0), 1)

# Draw a rectangle from x-,y-coordinates and width/height
def draw_rectangle(img, rec_attr):
    x,y,w,h = rec_attr
    cv2.rectangle(img,(x,y),(x+w,y+h),(0,255,0),2)

# Measure the focus from a grayscale image
def measure_focus(roi_gray):
    focus = cv2.Laplacian(roi_gray, cv2.CV_64F).var()
    return focus / 1000 * 255