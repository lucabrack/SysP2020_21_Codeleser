# import image processing libraries
from picamera.array import PiRGBArray
from picamera import PiCamera
import cv2
import numpy as np
import math

from lib.enclosings import *

# Start Camera Module
def open_camera(camera_config, preview=False):
    if preview:
        w = int(camera_config['vid_width'])
        h = int(camera_config['vid_height'])
    else:
        w = int(camera_config['frame_width'])
        h = int(camera_config['frame_height'])
    resolution = (w,h)

    camera = PiCamera(resolution=resolution, framerate=int(camera_config['frame_rate']))
    
    return camera

# Convert image to grayscale
def grayscale(img):
    return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

# Convert image to BGR-Colorspace
def bgr(img):
    return cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)

# Find and return coordinates from Region Of Interest (ROI)
def get_roi_attr(img_gray, parameters):
    # Define all parameters from config file
    BLUR_FULL = int(parameters['blur_full'])
    THRESH_BLOCK_FULL = int(parameters['thresh_block_full'])
    THRESH_CONST_FULL = int(parameters['thresh_const_full'])

    # blur the image to filter out unwanted noise
    blur = cv2.medianBlur(img_gray,BLUR_FULL)

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
    x,y,w,h = roi_attr
    return img.copy()[y:y+h,x:x+w]

# Get all contours in the Region Of Interest (ROI)
def get_roi_contours(roi_gray, parameters):
    # Define all parameters from config file
    BLUR_ROI = int(parameters['blur_roi'])
    THRESH_BLOCK_ROI = int(parameters['thresh_block_roi'])
    THRESH_CONST_ROI = int(parameters['thresh_const_roi'])

    # blur the image to filter out unwanted noise
    roi_blur = cv2.medianBlur(roi_gray,BLUR_ROI)
    # Adaptive thresholding to get a black and white image
    roi_thresh = cv2.adaptiveThreshold(roi_blur,255,cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY_INV,THRESH_BLOCK_ROI,THRESH_CONST_ROI)
    # find the contours on the zoom image
    cont_roi, _ = cv2.findContours(roi_thresh, 1, 2)

    return cont_roi, roi_thresh


def draw_contours(img, contours):
    cv2.drawContours(img, contours, -1, (255,0,0), 1)

def draw_rectangle(img, rec_attr):
    x,y,w,h = rec_attr
    cv2.rectangle(img,(x,y),(x+w,y+h),(0,255,0),2)

def measure_focus(roi_gray):
    return cv2.Laplacian(roi_gray, cv2.CV_64F).var()

# Process and draw images
def get_preview(img, enclosure_func, parameters):   
    img_gray = grayscale(img)

    # Search for Region of Interest
    roi_attr, img_bin = get_roi_attr(img_gray, parameters)
    
    # Make a blank image for Resolution output
    focus_img = np.zeros((100,400,3), np.uint8)

    # Check if Region of Interest was found
    if roi_attr is not None:
        roi = get_roi(img, roi_attr)
        roi_gray = get_roi(img_gray, roi_attr)

        contours, roi_bin = get_roi_contours(roi_gray, parameters)
        
        # find contours
        # get the right enclosing for every contour found
        enc = []
        for c in contours:
            enc.append(enclosure_func(c))
        
        # We need every image in Color
        img_bin = bgr(img_bin) 
        roi_bin = bgr(roi_bin)

        # Draw all the Contours
        draw_rectangle(img, roi_attr)
        draw_rectangle(img_bin, roi_attr)
        draw_contours(roi, enc)
        draw_contours(roi_bin, enc)

        # Resize small images for concatenating (all images must be same size)
        roi_display = cv2.resize(roi, (img.shape[1],img.shape[0]))
        roi_bin_display = cv2.resize(roi_bin, (img.shape[1],img.shape[0]))

        # Measure the focus of the zoom image and draw it on the focus image
        fm = int(measure_focus(roi_gray))
        font = cv2.FONT_HERSHEY_SIMPLEX
        text = "Focus: " + str(fm)
        textsize = cv2.getTextSize(text, font, 1, 2)[0]
        textX = 20
        textY = int((focus_img.shape[0] + textsize[1]) / 2)
        cv2.putText(focus_img, text, (textX, textY), font, 1, (255, 255, 255), 2)

    else: # No Contours were found -> display black images
        img_bin = bgr(img_bin) # We need every image in Color
        roi_display = np.zeros_like(img)
        roi_bin_display = roi_display.copy()


    return img, img_bin, roi_display, roi_bin_display, focus_img

