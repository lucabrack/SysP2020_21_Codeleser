from picamera.array import PiRGBArray
from picamera import PiCamera
import cv2
import time

class Camera:
    def __init__(self, camera_config, preview=False):
        if preview:
            w = int(camera_config['vid_width'])
            h = int(camera_config['vid_height'])
        else:
            w = int(camera_config['frame_width'])
            h = int(camera_config['frame_height'])
        self.resolution = (w,h)
        self.framerate = int(camera_config['frame_rate'])
        self.format = 'bgr'

    def open(self):
        self.camera = PiCamera(resolution=self.resolution, framerate=self.framerate)
        time.sleep(5)
        print("Camera opened")
    
    def close(self):
        self.camera.close()

    def capture_image(self):
        with PiRGBArray(self.camera) as rawCapture:
            self.camera.capture(rawCapture, format=self.format, use_video_port=True)
            return rawCapture.array