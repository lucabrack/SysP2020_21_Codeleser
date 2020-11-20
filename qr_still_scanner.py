import cv2
import numpy as np
from picamera.array import PiRGBArray
from picamera import PiCamera
import time

print("Starting Camera")
camera = PiCamera()
rawCapture = PiRGBArray(camera)

time.sleep(0.1)

qr_detector = cv2.QRCodeDetector()

def draw_qr_detection(img, pts, data):
    pts = np.int32(pts).reshape(-1,2)
    
    for j in range(pts.shape[0]):
        cv2.line(img, tuple(pts[j]), tuple(pts[(j+1) % pts.shape[0]]), (0, 255, 0), 5)
    
    for j in range(pts.shape[0]):
        cv2.circle(img, tuple(pts[j]), 10, (0, 0, 255), -1)
        
    image = cv2.putText(img, data, (10, 30), cv2.FONT_HERSHEY_SIMPLEX,
                   1, (255, 0, 0), 2, cv2.LINE_AA)

def read_qr(image):
    data, bbox, qr_code = qr_detector.detectAndDecode(image)

    if len(data) > 0:
        draw_qr_detection(image, bbox, data)
    
camera.capture(rawCapture, format="bgr")
image = rawCapture.array

read_qr(image)

cv2.imshow("Image", image)
cv2.waitKey(0)