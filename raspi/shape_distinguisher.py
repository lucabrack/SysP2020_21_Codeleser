import os
import argparse
import time
from configparser import ConfigParser

from picamera.array import PiRGBArray
from picamera import PiCamera
import cv2
import numpy as np

parser = argparse.ArgumentParser(description="Shape Distinguisher")
parser.add_argument("-c", "--commands", type=str, 
                    help="Give Features that should be displayed/printed out")
parser.add_argument("-f", "--focus", nargs='+', type=str, 
                    help="Give Features that should be displayed/printed out")
args = parser.parse_args()

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

feature_parser = {
    'c'    : centroid,
    'a'    : area,
    'p'    : perimeter,
    'l'    : length
}


def init_camera():
    print("Initialize Camera")
    config = ConfigParser()
    config.read('raspi/config.ini')    
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
    image = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    image = cv2.medianBlur(image,5)
    image = cv2.adaptiveThreshold(image,255,cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,11,2)
    cont, _ = cv2.findContours(image, 1, 2)
    enclosure = cont

    


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
        image = process_image(image, args.commands)
        cv2.imshow("Preview Video", image)
        key = cv2.waitKey(1) & 0xFF
        rawCapture.truncate(0) #empty output for next Image

        # Break if 'q' key is pressed
        if key == ord('q'):
            break

print("Terminating Program!")