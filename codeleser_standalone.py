# import important system libraries
import os
import sys
sys.path.append('raspi')

# import image processing libraries
import cv2

# import project libraries
from raspi.image_info import get_image_info
from raspi.lib.config_reader import ConfigReader

if __name__ == "__main__":
    # Read the config file
    config = ConfigReader()
    w = int(config.param['camera_parameters']['frame_width'])
    h = int(config.param['camera_parameters']['frame_height'])

    image = cv2.imread('00_image.png')
    image = cv2.resize(image,(w,h))
    

    # Read and save all the image infos
    get_image_info(image, config.param['image_parameters'], debug_folder_path='./tmp_imgs/')