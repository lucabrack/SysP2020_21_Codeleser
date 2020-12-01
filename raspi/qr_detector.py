import os
import argparse
import time
from configparser import ConfigParser

from picamera.array import PiRGBArray
from picamera import PiCamera
import cv2
import numpy as np


parser = argparse.ArgumentParser(description="Control Raspi Cam")
parser.add_argument("-pv", "--preview_video", action="store_true",
                    help="Preview Camera Input as Video Stream in small window. Kill with 'q'")
parser.add_argument("-ps", "--preview_still", action="store_true",
                    help="Preview Camera Input as Still Image in window. Kill with any Keyboard Input. Press 's' to save image")
parser.add_argument("-o", "--output", action="store_true",
                    help="Store Image. Either the last one of a preview or a new one without Preview.")
parser.add_argument("-fm", "--focus_measure", action="store_true",
                    help="Measure the sharpness of the image. The higher the value the more in focus the image is.")
parser.add_argument("-qr", "--detect_qr", action="store_true",
                    help="Detect and Draw QR-Codes.")
args = parser.parse_args()


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


def process_image(img, pts, data, args):

    # Detect and draw QR-Code
    if args.detect_qr:
        qrCodeDetector = cv2.QRCodeDetector()
        decodedText, points, _ = qrCodeDetector.detectAndDecode(image)
        if points is not None:
            pts = np.int32(pts).reshape(-1,2)            
            for j in range(pts.shape[0]):
                cv2.line(img, tuple(pts[j]), tuple(pts[(j+1) % pts.shape[0]]), (0, 255, 0), 5)                
            image = cv2.putText(img, data, (10, 30), cv2.FONT_HERSHEY_SIMPLEX,
                        1, (255, 0, 0), 2, cv2.LINE_AA)

    # Measure and print out bluriness
    if args.focus_measure:
        img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        fm = cv2.Laplacian(img_gray, cv2.CV_64F).var()
        print("Focus Measure: " + str(fm))


camera_config = init_camera()
print("Starting Preview")
with open_camera(camera_config, video=True) as camera:
    rawCapture = PiRGBArray(camera)

    for frame in camera.capture_continuous(rawCapture, format='bgr', use_video_port=True):
        image = frame.array
        qr_detection()
        cv2.imshow("Preview Video", image)
        key = cv2.waitKey(1) & 0xFF
        rawCapture.truncate(0) #empty output for next Image

        # Break if 'q' key is pressed
        if key == ord('q'):
            break

print("Terminating Program!")