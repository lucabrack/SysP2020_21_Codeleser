# import important system libraries
import os
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
config.read('./raspi/config.ini')

# Start Camera
print("Starting Camera")
with img_proc.open_camera(config['camera_parameters']) as camera:
    rawCapture = PiRGBArray(camera)
    time.sleep(0.1)
    print("Camera opened")

    camera.capture(rawCapture, format='bgr')
    image = rawCapture.array


    img_proc.get_image_infos(image, config['image_parameters'])