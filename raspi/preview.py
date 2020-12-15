# import important system libraries
import os
import sys
import argparse
import time
from configparser import ConfigParser

# import image processing libraries
import cv2
from picamera.array import PiRGBArray
import numpy as np

# import project libraries
from lib.enclosings import *
import lib.image_processing as img_proc
from lib.config_reader import ConfigReader
from lib.cam import Camera

## Get all 4 Images for the live Preview, plus the focus image
def get_preview(img, enclosure_func, image_parameters):   
    img_gray = img_proc.grayscale(img)

    # Search for Region of Interest
    roi_attr, img_bin = img_proc.get_roi_attr(img_gray, image_parameters)
    
    # Make a blank image for Resolution output
    focus_img = np.zeros((100,400,3), np.uint8)

    # Check if Region of Interest was found
    if roi_attr is not None:
        roi = img_proc.get_roi(img, roi_attr)
        roi_gray = img_proc.get_roi(img_gray, roi_attr)

        contours, roi_bin = img_proc.get_roi_contours(roi_gray, image_parameters)
        
        # find contours
        # get the right enclosing for every contour found
        enc = []
        for c in contours:
            enc.append(enclosure_func(c))
        
        # We need every image in Color
        img_bin = img_proc.bgr(img_bin) 
        roi_bin = img_proc.bgr(roi_bin)

        # Draw all the Contours
        img_proc.draw_rectangle(img, roi_attr)
        img_proc.draw_rectangle(img_bin, roi_attr)
        img_proc.draw_contours(roi, enc)
        img_proc.draw_contours(roi_bin, enc)

        # Resize small images for concatenating (all images must be same size)
        roi_display = cv2.resize(roi, (img.shape[1],img.shape[0]))
        roi_bin_display = cv2.resize(roi_bin, (img.shape[1],img.shape[0]))

        # Measure the focus of the zoom image and draw it on the focus image
        fm = int(img_proc.measure_focus(roi_gray))
        font = cv2.FONT_HERSHEY_SIMPLEX
        text = "Focus: " + str(fm)
        textsize = cv2.getTextSize(text, font, 1, 2)[0]
        textX = 20
        textY = int((focus_img.shape[0] + textsize[1]) / 2)
        cv2.putText(focus_img, text, (textX, textY), font, 1, (255, 255, 255), 2)

    else: # No Contours were found -> display black images
        img_bin = img_proc.bgr(img_bin) # We need every image in Color
        roi_display = np.zeros_like(img)
        roi_bin_display = roi_display.copy()


    return img, img_bin, roi_display, roi_bin_display, focus_img


## Method for the trackbars to change the parameters
def change_image_param(val, tb_name):
    config.param['image_parameters'][tb_name] = str(val)


## Create a second window with all the trackbars
def create_param_window(win_name):
    cv2.namedWindow(win_name)
    cv2.createTrackbar('blur_full', win_name, int(config.param['image_parameters']['blur_full']), 100, lambda x: change_image_param(x, 'blur_full'))
    cv2.createTrackbar('block_full', win_name, int(config.param['image_parameters']['thresh_block_full']), 100, lambda x: change_image_param(x, 'thresh_block_full'))
    cv2.createTrackbar('const_full', win_name, int(config.param['image_parameters']['thresh_const_full']), 100, lambda x: change_image_param(x, 'thresh_const_full'))
    cv2.createTrackbar('blur_roi', win_name, int(config.param['image_parameters']['blur_roi']), 100, lambda x: change_image_param(x, 'blur_roi'))
    cv2.createTrackbar('block_roi', win_name, int(config.param['image_parameters']['thresh_block_roi']), 100, lambda x: change_image_param(x, 'thresh_block_roi'))
    cv2.createTrackbar('const_roi', win_name, int(config.param['image_parameters']['thresh_const_roi']), 100, lambda x: change_image_param(x, 'thresh_const_roi'))


## Start live preview
if __name__ == "__main__":
    print("Starting Preview")

    config = ConfigReader()
    cam = Camera(config.param['camera_parameters'], preview=True)
    cam.open()
    
    enclosure = contour # default enclosure
    create_param_window('Parameters')
        
    for frame in cam.capture_continous():
        image = frame.array
        # Get the 4 Images for the preview and the focus image
        img, img_bin, roi, roi_bin, focus_img = get_preview(image, enclosure, config.param['image_parameters'])

        # concat the 4 images to one big one
        result0 = cv2.hconcat([img, img_bin]) 
        result1 = cv2.hconcat([roi, roi_bin])
        result = cv2.vconcat([result0, result1])
        result = cv2.resize(result, (int(config.param['display_parameters']['preview_width']),
                                    int(config.param['display_parameters']['preview_height'])))

        # display in separate window
        cv2.imshow("Preview", result)
        cv2.imshow('Parameters', focus_img)
        key = cv2.waitKey(1) & 0xFF
        cam.truncate_output()

        # Break if 'q' key is pressed
        if key == ord('q'):
            break

        # Save parameters if 's' key is pressed
        elif key == ord('s'):
            config.write_param()            

        # If a key from our enclosure list is pressed, change the
        # enclosure method
        elif chr(key) in enclosure_parser:
            print(enclosure_parser[chr(key)].__name__)
            enclosure = enclosure_parser[chr(key)]


    print("Terminating Program!")
    cam.close()
    cv2.destroyAllWindows() # close all windows