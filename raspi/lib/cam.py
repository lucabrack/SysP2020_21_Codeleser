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
        self.rawCapture = PiRGBArray(self.camera)
        time.sleep(2)
        print("Camera opened")
    
    def close(self):
        self.camera.close()

    def capture_image(self):
        self.truncate_output()
        self.camera.capture(self.rawCapture, format=self.format)
        return self.rawCapture.array

    def capture_continous(self):
        return self.camera.capture_continuous(self.rawCapture,
                    format=self.format, use_video_port=True)

    def truncate_output(self):
        self.rawCapture.truncate(0) #empty output for next Image