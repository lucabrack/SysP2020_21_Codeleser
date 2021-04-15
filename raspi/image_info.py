# import important system libraries
import os
import sys
import re
import time
import shutil
from datetime import datetime

# import image processing libraries
import cv2
import numpy as np

# import project libraries
from lib.enclosings import *
from lib.contour_features import *
import lib.image_processing as img_proc


## Get all infos of every contour found
def get_image_info(img, image_parameters, save_imgs=True, debug_folder_path='./raspi/debug/', max_saves=10):
    # All the infos get saved in one list
    info_list = []
    
    img_gray = img_proc.grayscale(img)
    
    img_gray_resized = cv2.resize(img_gray,(412,308))
    
    # Search for Region of Interest
    roi_attr, img_bin = img_proc.get_roi_attr(img_gray_resized, image_parameters)

    # save the images for debugging purposes
    if save_imgs:
        folder_path = create_img_folder(debug_folder_path, max_saves=max_saves)
        save_img(folder_path, "00_img", cv2.resize(img,(412,308)))
        img_bin_bgr = img_proc.bgr(img_bin.copy())
        if roi_attr is not None:
            img_proc.draw_rectangle(img_bin_bgr, roi_attr)
        save_img(folder_path, "01_img_binarized", img_bin_bgr) 
    
    # Check if the Region of Interest was found
    if roi_attr is not None:
        # Get Centre and Area of Region of Interest, write them to the info string
        roi_x, roi_y = get_center_roi(roi_attr, img_gray_resized)
        roi_area_scaled = get_area_roi(roi_attr, img_gray_resized)
        info_list.append(roi_x)
        info_list.append(roi_y)
        info_list.append(roi_area_scaled)
        
        if 5 <= roi_area_scaled <= 13: #Check if the ROI is a probable size
            # Make ROI gray and search for contours
            roi_gray = img_proc.get_roi(img_gray, tuple([x*8 for x in roi_attr]))    
            contours, roi_bin = img_proc.get_roi_contours(roi_gray, image_parameters)

            # Measure focus of ROI write it to info string 
            info_list.append(int(img_proc.measure_focus(roi_gray)))

            # Save images for debugging purposes
            if save_imgs:
                save_img(folder_path, "02_roi", roi_gray)
                save_img(folder_path, "03_roi_binarized", roi_bin)

            shapes = img_proc.get_shapes(contours, roi_gray)
            info_list.append(len(shapes))
            for shape in shapes:
                info_list.append(shape[0])
                info_list.append(shape[1][0])
                info_list.append(shape[1][1])

            # save images and info string for debugging purposes
            if save_imgs:
                roi_copy = img_proc.bgr(roi_gray.copy())
                img_proc.draw_contours(roi_copy, contours)
                save_img(folder_path, '04_contour', roi_copy)
                '''
                roi_copy = img_proc.bgr(roi_gray.copy())
                img_proc.draw_contours(roi_copy, circle(contours))
                save_img(folder_path, '05_circle', roi_copy)
                roi_copy = img_proc.bgr(roi_gray.copy())
                img_proc.draw_contours(roi_copy, box(contours))
                save_img(folder_path, '05_rectangle', roi_copy)
                roi_copy = img_proc.bgr(roi_gray.copy())
                img_proc.draw_contours(roi_copy, hull(contours))
                save_img(folder_path, '05_hull', roi_copy)
                '''
                

    else: # Region of Interest was not found
        info_list.append(4)
        info_list.append(0)
        info_list.append(4)
        print("Region of Interest not found.")

    save_info_list(folder_path, info_list)
    return info_list


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


## Save the info string
def save_info_list(folder_path, info_list):
    # if the folder path doesn't exist, nothing gets saved
    if folder_path is not None:
        with open(os.path.join(folder_path, "image_infos.txt"), 'w') as txt:
            txt.write(str(info_list))
    else:
        print("Info String could not be saved.")
        print("Folder Path " + str(folder_path) + " does not exist.")


## Main method
if __name__ == "__main__":
    from picamera.array import PiRGBArray
    from lib.cam import Camera
    from lib.config_reader import ConfigReader

    # Read the config file
    config = ConfigReader()

    print("Starting Camera")
    cam = Camera(config.param['camera_parameters'])
    cam.open()
    image = cam.capture_image()
    print("Image captured")

    # Read and save all the image infos
    get_image_info(image, config.param['image_parameters'])
    print("Done")

    cam.close()