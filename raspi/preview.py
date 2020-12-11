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


## Read config file
config = ConfigParser()
if os.path.exists('config.ini'):
    config.read('config.ini')
elif os.path.exists('./raspi/config.ini'):
    config.read('./raspi/config.ini')
else:
    sys.exit('ERROR: No config file found!')

def change_image_param(val, tb_name):
    config['image_parameters'][tb_name] = str(val)

def create_param_window(win_name):
    cv2.namedWindow(win_name)
    cv2.createTrackbar('blur_full', win_name, int(config['image_parameters']['blur_full']), 100, lambda x: change_image_param(x, 'blur_full'))
    cv2.createTrackbar('block_full', win_name, int(config['image_parameters']['thresh_block_full']), 100, lambda x: change_image_param(x, 'thresh_block_full'))
    cv2.createTrackbar('const_full', win_name, int(config['image_parameters']['thresh_const_full']), 100, lambda x: change_image_param(x, 'thresh_const_full'))
    cv2.createTrackbar('blur_roi', win_name, int(config['image_parameters']['blur_roi']), 100, lambda x: change_image_param(x, 'blur_roi'))
    cv2.createTrackbar('block_roi', win_name, int(config['image_parameters']['thresh_block_roi']), 100, lambda x: change_image_param(x, 'thresh_block_roi'))
    cv2.createTrackbar('const_roi', win_name, int(config['image_parameters']['thresh_const_roi']), 100, lambda x: change_image_param(x, 'thresh_const_roi'))

# Start live preview
print("Starting Preview")
with img_proc.open_camera(config['camera_parameters'], preview=True) as camera:
    rawCapture = PiRGBArray(camera)
    enclosure = contour # default enclosure
    create_param_window('Parameters')
    
    for frame in camera.capture_continuous(rawCapture, format='bgr', use_video_port=True):
        image = frame.array
        # Get the 4 Images for the preview and the focus image
        img, img_bin, roi, roi_bin, focus_img = img_proc.get_preview(image, enclosure, config['image_parameters'])

        # concat the 4 images to one big one
        result0 = cv2.hconcat([img, img_bin]) 
        result1 = cv2.hconcat([roi, roi_bin])
        result = cv2.vconcat([result0, result1])
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