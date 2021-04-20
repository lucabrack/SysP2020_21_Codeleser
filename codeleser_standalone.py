# import important system libraries
import os
import sys
sys.path.append('raspi')
from time import sleep

# import GUI libs
import tkinter as tk
from tkinter import filedialog

# import image processing libraries
import cv2

# import project libraries
from raspi.image_info import get_image_info
from raspi.lib.config_reader import ConfigReader


class GUI(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.master = master
        self.pack()
        self.create_widgets()
        self.input_files = []
        self.output_folder = ''

    def create_widgets(self):
        self.button_open_if = tk.Button(self, text="Select Input Files",
                                        command=self.def_input_files)
        self.button_open_if.grid(row=0,column=1)

        self.listbox_inputfiles = tk.Listbox(self, height=10, width=100)
        self.listbox_inputfiles.grid(row=0,column=0)

        self.button_open_of = tk.Button(self, text="Select Output Directory",
                                        command=self.def_output_folder)
        self.button_open_of.grid(row=1,column=1)

        self.listbox_outputfolder = tk.Listbox(self, height=1, width=100)
        self.listbox_outputfolder.grid(row=1,column=0)

        self.start = tk.Button(self, text="START", fg="green", height=1, width=30,
                                        command=self.start_machine_vision)
        self.start.grid(row=2,column=0)

        self.exit = tk.Button(self, text="EXIT", fg="red", height=1, width=10,
                              command=self.master.destroy)
        self.exit.grid(row=2,column=1)

        col_count, row_count = self.grid_size()

        for col in range(col_count):
            self.grid_columnconfigure(col, minsize=150)
        for row in range(row_count):
            self.grid_rowconfigure(row, minsize=30)

    def def_input_files(self):
        self.input_files = list(filedialog.askopenfilenames(title="Select Input Images", filetypes = [("image",('.png', '.jpg', '.jpeg', '.gif', '.bmp'))]))
        self.listbox_inputfiles.delete(0, tk.END)
        self.listbox_inputfiles.insert(tk.END, *self.input_files)

    def def_output_folder(self):
        self.output_folder = filedialog.askdirectory(title="Select Output Directory")
        self.listbox_outputfolder.delete(0, tk.END)
        self.listbox_outputfolder.insert(tk.END, self.output_folder)

    def start_machine_vision(self):
        if len(self.input_files) * len(self.output_folder) > 0:
            # Read the config file
            config = ConfigReader()
            w = int(config.param['camera_parameters']['frame_width'])

            for img_file in self.input_files:
                image = cv2.imread(img_file)

                # Resize the image to config-defined size
                ratio = w / image.shape[1]
                image = cv2.resize(image, (w , int(image.shape[0]*ratio)))

                # Read and save all the image infos
                get_image_info(image, config.param['image_parameters'], debug_folder_path=self.output_folder, max_saves=9999)

                # Sleep for a second because the images are stored with timestamp names
                sleep(1)
                

    
if __name__ == '__main__':
    root = tk.Tk()
    root.title("Image Processing Standalone")
    gui = GUI(master=root)
    gui.mainloop()   