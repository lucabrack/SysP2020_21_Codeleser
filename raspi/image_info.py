# import important system libraries
import os
import sys
import re
import time
import shutil
from datetime import datetime

# import image processing libraries
import cv2
from picamera.array import PiRGBArray
import numpy as np

# import project libraries
from lib.enclosings import *
from lib.contour_features import *
import lib.image_processing as img_proc
from lib.config_reader import ConfigReader
from lib.cam import Camera

# Define root path to save the debugging images
ROOT_SAVE_PATH = './raspi/debug/'


## Get all infos of every contour found
def get_image_info(img, image_parameters, save_imgs=True):
    # All the infos get saved in one consecutive string
    info_str = ""
    
    img_gray = img_proc.grayscale(img)
    
    # Search for Region of Interest
    roi_attr, img_bin = img_proc.get_roi_attr(img_gray, image_parameters)

    # save the images for debugging purposes
    if save_imgs:
        folder_path = create_img_folder(ROOT_SAVE_PATH)
        save_img(folder_path, "00_img", img)
        img_bin_bgr = img_proc.bgr(img_bin.copy())
        if roi_attr is not None:
            img_proc.draw_rectangle(img_bin_bgr, roi_attr)
        save_img(folder_path, "01_img_binarized", img_bin_bgr) 
    
    # Check if the Region of Interest was found
    if roi_attr is not None:
        # Get Centre and Area of Region of Interest, write them to the info string
        roi_x, roi_y = get_center_roi(roi_attr, img)
        roi_area, roi_area_scaled = get_area_roi(roi_attr, img)
        info_str = build_info_str(info_str, roi_x)
        info_str = build_info_str(info_str, roi_y)
        info_str = build_info_str(info_str, roi_area_scaled)
        
        # Make ROI gray and search for contours
        roi_gray = img_proc.get_roi(img_gray, roi_attr)    
        contours, roi_bin = img_proc.get_roi_contours(roi_gray, image_parameters)

        # Measure focus of ROI, get number of contours found, write them to info string 
        info_str = build_info_str(info_str, int(img_proc.measure_focus(roi_gray)))
        info_str = build_info_str(info_str, len(contours))

        # Save images for debugging purposes
        if save_imgs:
            save_img(folder_path, "02_roi", roi_gray)
            save_img(folder_path, "03_roi_binarized", roi_bin)

        if 'n' in enclosure_parser:
            del enclosure_parser['n'] # delete the 'none' item, as it serves no purpose here
        enclose_funcs = list(enclosure_parser.values())

        # loop through all enclosing functions
        for i, enclose_func in enumerate(enclose_funcs):
            enc = []
            # write the name of the function to the info string
            info_str = build_info_str(info_str, enclose_func.__name__)

            # loop through all contours found in the ROI
            for c in contours:
                enclosing = enclose_func(c) 
                enc.append(enclosing)

                # calculate the different features, write them to the info string
                cx, cy = get_center(enclosing, roi_gray)
                area = get_area(enclosing, roi_area)
                perimeter = get_perimeter(enclosing, roi_area)
                #orientation = get_orientation(enclosing) #opted out from giving orientation
                point_count = get_point_count(enclosing, None)
                info_str = build_info_str(info_str, cx)
                info_str = build_info_str(info_str, cy)
                info_str = build_info_str(info_str, area)
                info_str = build_info_str(info_str, perimeter)
                info_str = build_info_str(info_str, point_count)

            # save images and info string for debugging purposes
            if save_imgs:
                roi_copy = img_proc.bgr(roi_gray.copy())
                img_proc.draw_contours(roi_copy, enc)
                save_img(folder_path, f'{i+4:02d}_roi_' + enclose_func.__name__, roi_copy)
                with open(os.path.join(folder_path, "image_infos.txt"), 'w') as txt:
                    txt.write(info_str)

    else: # Region of Interest was not found
        info_str = "NothingFound"
        print("Region of Interest not found.")

    return info_str


## Create and return image folder and delete old ones
def create_img_folder(root_path, max_saves=10):
    # The path has to exist
    if not os.path.exists(root_path):
        print("Images can not be saved, because " + root_path + " does not exist.")
        return None
    
    # If there are too much folders present delete the oldest ones
    r = re.compile('.*-.*-.*_.*-.*-') # Define the format of the folders
    # list all folders that match this format
    folders = [os.path.join(root_path, x) for x in os.listdir(root_path) if r.match(x) is not None]
    while len(folders) >= max_saves:
        # Search for the oldest folder, delete it, and update the folder list
        oldest_folder = min(folders, key=os.path.getctime)
        shutil.rmtree(oldest_folder)
        folders = [os.path.join(root_path, x) for x in os.listdir(root_path) if r.match(x) is not None]
    
    # Make a folder with the current timestamp as the name
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    folder_path = os.path.join(root_path, timestamp)
    os.mkdir(folder_path)

    return folder_path


## Save the image as a png
def save_img(folder_path, img_name, img):
    # if the folder path doesn't exist, nothing gets saved
    if folder_path is not None:
        full_path = os.path.join(folder_path, img_name + '.png')
        success = cv2.imwrite(full_path, img)
        if not success:
            print("Saving image " + full_path + " failed.")


## Build the info string
def build_info_str(info_str, value):
    # All the infos get seperated with commas
    if len(info_str) > 0:
        info_str += ','

    # all types get casted to string
    if isinstance(value, int):
        info_str += str(value)
    elif isinstance(value, float):
        info_str += f'{value:.6f}'
    elif isinstance(value, str):
        info_str += value
    else:
        print('Unhandled instance for info string: ' + str(type(value)))
    return info_str


## Main method
if __name__ == "__main__":
    # Read the config file
    config = ConfigReader()

    print("Starting Camera")
    cam = Camera(config.param['camera_parameters'])
    cam.open()
    image = cam.capture_image()

    # Read and save all the image infos
    get_image_info(image, config.param['image_parameters'])

    cam.close()