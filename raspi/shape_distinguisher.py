import os
import argparse
import time
from configparser import ConfigParser

from picamera.array import PiRGBArray
from picamera import PiCamera
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

# Initialize Camera, read config file
def init_camera():
    print("Initialize Camera")
    config = ConfigParser()
    if os.path.exists('raspi/config.ini'):
        config.read('raspi/config.ini')
    else:
        config.read('config.ini')
    camera_config = dict(config.items('camera_parameters'))

    return camera_config

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
def process_image(img, enclosure_func):

    # Find the black rectangle border
    copy = img.copy()
    gray = cv2.cvtColor(copy, cv2.COLOR_BGR2GRAY)
    blur = cv2.medianBlur(gray,19)
    thresh = cv2.adaptiveThreshold(blur,255,cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY_INV,59,20)
    fill = thresh.copy()
    h, w = fill.shape[:2]
    mask = np.zeros((h+2,w+2), np.uint8)
    cv2.floodFill(fill, mask, (0,0), 255)
    fill_inv = cv2.bitwise_not(fill)
    img_thresh = thresh | fill_inv
    cont, _ = cv2.findContours(img_thresh, 1, 2)
    img_thresh = cv2.cvtColor(img_thresh, cv2.COLOR_GRAY2BGR)
    
    # Check if any contours were found
    if len(cont) > 0:
        c = max(cont, key = cv2.contourArea) # find contour with biggest Area
        x,y,w,h = cv2.boundingRect(c)

        # From now on, we only work with the area inside the rectangle border
        zoom = img.copy()[y:y+h,x:x+w]
        zoom_gray = gray.copy()[y:y+h,x:x+w]
        
        zoom_blur = cv2.medianBlur(zoom_gray,3)
        zoom_thresh = cv2.adaptiveThreshold(zoom_blur,255,cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY_INV,59,10)

        cont_zoom, _ = cv2.findContours(zoom_thresh, 1, 2) # find contours
        enc = []
        # get the right enclosing for every contour found
        for c in cont_zoom:
            enc.append(enclosure_func(c))
        
        # Draw all the Contours
        cv2.rectangle(img_thresh,(x,y),(x+w,y+h),(0,255,0),2)
        cv2.rectangle(img,(x,y),(x+w,y+h),(0,255,0),2)
        cv2.drawContours(zoom, enc, -1, (255,0,0), 1)
        zoom_thresh = cv2.cvtColor(zoom_thresh, cv2.COLOR_GRAY2BGR) # We need every image in Color
        cv2.drawContours(zoom_thresh, enc, -1, (255,0,0), 1)

        # Resize small images for concatenating
        zoom_display = cv2.resize(zoom, (img.shape[1],img.shape[0]))
        zoom_thresh_display = cv2.resize(zoom_thresh, (img.shape[1],img.shape[0]))

    else: # No Contours were found -> display black images
        zoom_display = np.zeros_like(img)
        zoom_thresh_display = zoom_display.copy()


    return img, img_thresh, zoom_display, zoom_thresh_display


def measure_focus(img):
    # Measure and print out bluriness
    img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    fm = cv2.Laplacian(img_gray, cv2.CV_64F).var()
    print("Focus Measure: " + str(fm))


# Start live preview
print("Starting Preview")
with open_camera(init_camera(), video=True) as camera:
    rawCapture = PiRGBArray(camera)
    enclosure = contour # default enclosure

    for frame in camera.capture_continuous(rawCapture, format='bgr', use_video_port=True):
        image = frame.array
        image, thresh, zoom, zoom_thresh = process_image(image, enclosure) # process the image

        # concat the 4 images to one big one
        result0 = cv2.hconcat([image,thresh])
        result1 = cv2.hconcat([zoom,zoom_thresh])
        result = cv2.vconcat([result0,result1])
        result = cv2.resize(result, (1024,728))

        # display in separate window
        cv2.imshow("Preview Video", result)
        key = cv2.waitKey(1) & 0xFF
        rawCapture.truncate(0) #empty output for next Image

        # Break if 'q' key is pressed
        if key == ord('q'):
            break
        # Save last image if 's' key is pressed
        elif key == ord('s'):
            cv2.imwrite('image.png',image)
            print('Image saved')
        # If a key from our enclosure list is pressed, change the
        # enclosure method
        elif chr(key) in enclosure_parser:
            print(enclosure_parser[chr(key)].__name__)
            enclosure = enclosure_parser[chr(key)]

print("Terminating Program!")
cv2.destroyAllWindows() # close all windows