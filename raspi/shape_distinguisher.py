import os
import argparse
import time
from configparser import ConfigParser

from picamera.array import PiRGBArray
from picamera import PiCamera
import cv2
import numpy as np


def contour(image, contours):
        return contours

def approximation(image, contours):
    epsilon = 0.1*cv2.arcLength(contours,True)
    approx = cv2.approxPolyDP(contours,epsilon,True)
    return approx

def hull(image, contours):
    h = cv2.convexHull(contours)
    return h

def rectangle(image, contours):
    x,y,w,h = cv2.boundingRect(contours)
    rect = np.array([[x,y],[x+w,y],[x+w,y+h],[x,y+h]])
    return rect

def box(image, contours):
    min_rect = cv2.minAreaRect(contours)
    b = cv2.boxPoints(min_rect)
    b = np.int0(b)
    return b

def circle(image, contours):
    (x,y),radius = cv2.minEnclosingCircle(contours)
    center = (int(x),int(y))
    radius = int(radius)
    c = []
    for a in np.linspace(0.0, 2*math.pi, num=250):
        x = center[0] + radius*math.cos(a)
        y = center[1] + radius*math.sin(a)
        c.append([x,y])
    c = np.array(c, dtype='int64')
    return c

enclosure_parser = {
    'c'    : contour,
    'a'    : approximation,
    'h'    : hull,
    'r'    : rectangle,
    'b'    : box,
    'k'    : circle
}


def init_camera():
    print("Initialize Camera")
    config = ConfigParser()
    if os.path.exists('raspi/config.ini'):
        config.read('raspi/config.ini')
    else:
        config.read('config.ini')
    camera_config = dict(config.items('camera_parameters'))

    return camera_config


def open_camera(camera_config, video=False):
    if video:
        w = int(camera_config['vid_width'])
        h = int(camera_config['vid_height'])
    else:
        w = int(camera_config['frame_width'])
        h = int(camera_config['frame_height'])
    resolution = (w,h)

    camera = PiCamera(resolution=resolution, framerate=int(camera_config['frame_rate']))

    time.sleep(2) # Wait for the automatic gain control to settle
    
    return camera


def process_image(img, commands):
    copy = img.copy()
    gray = cv2.cvtColor(copy, cv2.COLOR_BGR2GRAY)
    blur = cv2.medianBlur(gray,5)
    thresh = cv2.adaptiveThreshold(blur,255,cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY_INV,11,2)
    fill = thresh.copy()
    h, w = fill.shape[:2]
    mask = np.zeros((h+2,w+2), np.uint8)
    cv2.floodFill(fill, mask, (0,0), 255)
    fill_inv = cv2.bitwise_not(fill)
    im_out = thresh | fill_inv    
    cont, _ = cv2.findContours(im_out, 1, 2)
    cont = cont[:-1]
    c = max(cont, key = cv2.contourArea)
    x,y,w,h = cv2.boundingRect(c)
    im_out = cv2.cvtColor(im_out, cv2.COLOR_GRAY2BGR)
    cv2.drawContours(im_out, c, -1, (255,0,0), 3)

    zoom = img[y:y+h,x:x+w]
    zoom = cv2.resize(zoom, (img.shape[1],img.shape[0]))

    return im_out, zoom
   


def measure_focus(img):
    # Measure and print out bluriness
    img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    fm = cv2.Laplacian(img_gray, cv2.CV_64F).var()
    print("Focus Measure: " + str(fm))


camera_config = init_camera()
print("Starting Preview")
with open_camera(camera_config, video=True) as camera:
    rawCapture = PiRGBArray(camera)

    for frame in camera.capture_continuous(rawCapture, format='bgr', use_video_port=True):
        image = frame.array
        thresh, zoom = process_image(image, 'c')
        result0 = cv2.hconcat([image,thresh])
        result1 = cv2.hconcat([zoom,zoom])
        result = cv2.vconcat([result0,result1])
        cv2.imshow("Preview Video", result)
        key = cv2.waitKey(1) & 0xFF
        rawCapture.truncate(0) #empty output for next Image

        # Break if 'q' key is pressed
        if key == ord('q'):
            break
        elif key == ord('s'):
            cv2.imwrite('image.png',image)
            print('Image saved')

print("Terminating Program!")
cv2.destroyAllWindows()