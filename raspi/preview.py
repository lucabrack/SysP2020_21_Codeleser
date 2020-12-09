# import important system libraries
import os
import argparse
import time
from configparser import ConfigParser

# import image processing libraries
from picamera.array import PiRGBArray
from picamera import PiCamera
import cv2
import numpy as np
import math

# import project libraries
from lib.enclosings import *


## Read config file
config = ConfigParser()
config.read('config.ini')

# Start Camera Module
def open_camera(camera_config, video=False):
    if video:
        w = int(camera_config['vid_width'])
        h = int(camera_config['vid_height'])
    else:
        w = int(camera_config['frame_width'])
        h = int(camera_config['frame_height'])
    resolution = (w,h)

    camera = PiCamera(resolution=resolution, framerate=int(camera_config['frame_rate']))
    
    return camera

# Process and draw images
def process_image(img, enclosure_func, parameters):
    # Define all parameters from config file
    BLUR_FULL = int(parameters['blur_full'])
    THRESH_BLOCK_FULL = int(parameters['thresh_block_full'])
    THRESH_CONST_FULL = int(parameters['thresh_const_full'])
    BLUR_ZOOM = int(parameters['blur_zoom'])
    THRESH_BLOCK_ZOOM = int(parameters['thresh_block_zoom'])
    THRESH_CONST_ZOOM = int(parameters['thresh_const_zoom'])

    # Copy the original image, to save it from changes
    copy = img.copy()
    # Make it grayscale for the thresholding
    gray = cv2.cvtColor(copy, cv2.COLOR_BGR2GRAY)
    # blur the image to filter out unwanted noise
    blur = cv2.medianBlur(gray,BLUR_FULL)

    # create a blank image to draw focus on
    focus_img = np.zeros((100, 400, 3), np.uint8)

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
        x,y,w,h = cv2.boundingRect(c) # Enclose the biggest contour with a rectangle

        # From now on, we only work with the area inside the rectangle border
        zoom = img.copy()[y:y+h,x:x+w] # cut the area within the border out of the original image 
        zoom_gray = gray.copy()[y:y+h,x:x+w] # make the same but with the gray image (saves us the grayscaling)
        
        # blur the image to filter out unwanted noise
        zoom_blur = cv2.medianBlur(zoom_gray,BLUR_ZOOM)
        # Adaptive thresholding to get a black and white image
        zoom_thresh = cv2.adaptiveThreshold(zoom_blur,255,cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY_INV,THRESH_BLOCK_ZOOM,THRESH_CONST_ZOOM)
         
        # find the contours on the zoom image
        cont_zoom, _ = cv2.findContours(zoom_thresh, 1, 2) # find contours
        # get the right enclosing for every contour found
        enc = []
        for c in cont_zoom:
            enc.append(enclosure_func(c))
        
        # We need every image in Color
        img_thresh = cv2.cvtColor(img_thresh, cv2.COLOR_GRAY2BGR) 
        zoom_thresh = cv2.cvtColor(zoom_thresh, cv2.COLOR_GRAY2BGR)

        # Draw all the Contours        
        cv2.rectangle(img_thresh,(x,y),(x+w,y+h),(0,255,0),2)
        cv2.rectangle(img,(x,y),(x+w,y+h),(0,255,0),2)
        cv2.drawContours(zoom, enc, -1, (255,0,0), 1)
        cv2.drawContours(zoom_thresh, enc, -1, (255,0,0), 1)

        # Resize small images for concatenating (all images must be same size)
        zoom_display = cv2.resize(zoom, (img.shape[1],img.shape[0]))
        zoom_thresh_display = cv2.resize(zoom_thresh, (img.shape[1],img.shape[0]))

        # Measure the focus of the zoom image and draw it on the focus image
        fm = int(cv2.Laplacian(zoom_gray, cv2.CV_64F).var())
        font = cv2.FONT_HERSHEY_SIMPLEX
        text = "Focus: " + str(fm)
        textsize = cv2.getTextSize(text, font, 1, 2)[0]
        textX = 20 #int((focus_img.shape[1] - textsize[0]) / 2)
        textY = int((focus_img.shape[0] + textsize[1]) / 2)
        cv2.putText(focus_img, text, (textX, textY), font, 1, (255, 255, 255), 2)

    else: # No Contours were found -> display black images
        img_thresh = cv2.cvtColor(img_thresh, cv2.COLOR_GRAY2BGR) # We need every image in Color
        zoom_display = np.zeros_like(img)
        zoom_thresh_display = zoom_display.copy()
  

    return img, img_thresh, zoom_display, zoom_thresh_display, focus_img


def measure_focus(img):
    # Measure and print out bluriness
    img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    fm = cv2.Laplacian(img_gray, cv2.CV_64F).var()
    print("Focus Measure: " + str(fm))


def change_image_param(val, tb_name):
    if val > 1:
        if val % 2 == 1:
            config['image_parameters'][tb_name] = str(val)
        else:
            config['image_parameters'][tb_name] = str(val+1)

def create_param_window(win_name):
    cv2.namedWindow(win_name)
    cv2.createTrackbar('blur_full', win_name, int(config['image_parameters']['blur_full']), 51, lambda x: change_image_param(x, 'blur_full'))
    cv2.createTrackbar('block_full', win_name, int(config['image_parameters']['thresh_block_full']), 199, lambda x: change_image_param(x, 'thresh_block_full'))
    cv2.createTrackbar('const_full', win_name, int(config['image_parameters']['thresh_const_full']), 99, lambda x: change_image_param(x, 'thresh_const_full'))
    cv2.createTrackbar('blur_zoom', win_name, int(config['image_parameters']['blur_zoom']), 51, lambda x: change_image_param(x, 'blur_zoom'))
    cv2.createTrackbar('block_zoom', win_name, int(config['image_parameters']['thresh_block_zoom']), 199, lambda x: change_image_param(x, 'thresh_block_zoom'))
    cv2.createTrackbar('const_zoom', win_name, int(config['image_parameters']['thresh_const_zoom']), 99, lambda x: change_image_param(x, 'thresh_const_zoom'))

# Start live preview
print("Starting Preview")
with open_camera(config['camera_parameters'], video=True) as camera:
    rawCapture = PiRGBArray(camera)
    enclosure = contour # default enclosure
    create_param_window('Parameters')
    
    for frame in camera.capture_continuous(rawCapture, format='bgr', use_video_port=True):
        image = frame.array
        image, thresh, zoom, zoom_thresh, focus_img = process_image(image, enclosure, config['image_parameters']) # process the image

        # concat the 4 images to one big one
        result0 = cv2.hconcat([image,thresh])
        result1 = cv2.hconcat([zoom,zoom_thresh])
        result = cv2.vconcat([result0,result1])
        result = cv2.resize(result, (int(config['display_parameters']['preview_width']),
                                    int(config['display_parameters']['preview_height'])))

        # display in separate window
        cv2.imshow("Preview", result)
        cv2.imshow('Parameters', focus_img)
        key = cv2.waitKey(1) & 0xFF
        rawCapture.truncate(0) #empty output for next Image

        # Break if 'q' key is pressed
        if key == ord('q'):
            break

        # Save parameters if 's' key is pressed
        elif key == ord('s'):
            with open('config.ini', 'w') as configfile:
                config.write(configfile)
            print('Parameters saved')

        # If a key from our enclosure list is pressed, change the
        # enclosure method
        elif chr(key) in enclosure_parser:
            print(enclosure_parser[chr(key)].__name__)
            enclosure = enclosure_parser[chr(key)]


print("Terminating Program!")
cv2.destroyAllWindows() # close all windows