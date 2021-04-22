# import important system libraries
import os
from time import sleep

# import GUI libs
import tkinter as tk
from tkinter import filedialog

# import image processing libraries
import numpy as np
import cv2
from PIL import Image, ImageTk

# set up serial communication
import serial
import struct
from raspi.lib.config_reader import ConfigReader

config = ConfigReader()

'''
# import SSH libs
import paramiko
from scp import SCPClient

USER = 'pi'
PW = '1234'

ssh = paramiko.SSHClient()
ssh.load_system_host_keys()
ssh.connect(HOST, username=USER, password=PW)

with SCPClient(ssh.get_transport()) as scp:
    scp.get('/home/pi/Projekte/SysP2020_21_Codeleser/raspi/debug', local_path='D:\\tmp\\', recursive=True)
'''

class GUI(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.master = master
        self.pack()
        self.serial_answer = ''
        self.output_folder = ''
        self.code_img = array2image(np.ones((500,500,3), np.uint8)*255)
        self.create_widgets()
        

    def create_widgets(self):
        self.label_befehl = tk.Label(self, text='Befehl: ')
        self.label_befehl.grid(row=0,sticky='E')
        self.entry_befehl = tk.Entry(self, width=20)
        self.entry_befehl.insert(0,'ping')
        self.entry_befehl.grid(row=0,column=1,sticky='W')

        self.label_port = tk.Label(self, text='Port: ')
        self.label_port.grid(row=0,column=3,sticky='E')
        self.entry_port = tk.Entry(self, width=10)
        self.entry_port.insert(0,'COMx')
        self.entry_port.grid(row=0,column=4,sticky='W')

        self.label_bdrate = tk.Label(self, text='Speed: ')
        self.label_bdrate.grid(row=0,column=6,sticky='E')
        self.entry_bdrate = tk.Entry(self, width=10)
        self.entry_bdrate.insert(0,'9600')
        self.entry_bdrate.grid(row=0,column=7,sticky='W')

        self.button_senden = tk.Button(self, text="Senden",
                                        command=self.send_command)
        self.button_senden.grid(row=0,column=9)
    
        self.label_antwort = tk.Label(self, text='Antwort: ')
        self.label_antwort.grid(row=1)
        self.entry_antwort = tk.Entry(self, width=70)
        self.entry_antwort.grid(row=1,column=1,columnspan=9,sticky='W')      
        
        self.button_generate = tk.Button(self, text="Code generieren")
        self.button_generate.grid(row=2,column=3,columnspan=3)
        self.label_image = tk.Label(self,image=self.code_img)
        self.label_image.image = self.code_img
        self.label_image.grid(row=3,column=0,rowspan=1,columnspan=10)
        self.button_save = tk.Button(self, text="Code speichern")
        self.button_save.grid(row=4,column=3,columnspan=3)
        
        self.label_ip = tk.Label(self, text='IP-Adresse: ')
        self.label_ip.grid(row=6,column=0)
        self.entry_ip = tk.Entry(self, width=20)
        self.entry_ip.grid(row=6,column=1)
        self.entry_ip.insert(0, '0.0.0.0')

        self.label_user = tk.Label(self, text='User: ')
        self.label_user.grid(row=6,column=3,sticky='E')
        self.entry_user = tk.Entry(self, width=10)
        self.entry_user.grid(row=6,column=4,sticky='W')
        self.entry_user.insert(0, 'pi')

        self.label_pw = tk.Label(self, text='PW: ')
        self.label_pw.grid(row=6,column=5,sticky='E')
        self.entry_pw = tk.Entry(self, width=10)
        self.entry_pw.grid(row=6,column=6,sticky='W')
        self.entry_pw.insert(0, '1234')
        self.button_get_pics = tk.Button(self, text="Debug Bilder holen")
        self.button_get_pics.grid(row=6,column=7,columnspan=3, sticky='E')

        self.label_error = tk.Label(self, text='Error: ')
        self.label_error.grid(row=7)
        self.entry_error = tk.Entry(self, width=70)
        self.entry_error.grid(row=7,column=1,columnspan=9,sticky='W')

        col_count, row_count = self.grid_size()
        for col in range(col_count):
            self.grid_columnconfigure(col, minsize=30)
        for row in range(row_count):
            self.grid_rowconfigure(row, minsize=30)


    def send_command(self):
        try:
            with serial.Serial() as ser:
                ser.port = self.entry_port.get()
                ser.baudrate = int(self.entry_bdrate.get())
                ser.open()
                ser.reset_input_buffer()
                ser.reset_output_buffer()
                print("Serial openend")

                cmd = self.entry_befehl.get()
                print(cmd)
                ser.write(cmd.encode())
                ser.write(b'\r')

                print("Waiting for message...")
                recv_data = b''
                while True:
                    recv_byte = ser.read()
                    if recv_byte == b'\n':
                        break
                    recv_data += recv_byte
                print("Message recieved!")

                self.serial_answer = recv_data
                self.entry_antwort.delete(0,len(self.entry_antwort.get()))
                self.entry_antwort.insert(0, self.serial_answer)

        except Exception as e:
            self.entry_antwort.delete(0,len(self.entry_antwort.get()))
            self.entry_antwort.insert(0, e)



    def def_output_folder(self):
        self.output_folder = filedialog.askdirectory(title="Select Output Directory")
        self.listbox_outputfolder.delete(0, tk.END)
        self.listbox_outputfolder.insert(tk.END, self.output_folder)


def array2image(array):
    border_width = 20
    border = np.zeros((array.shape[0] + border_width*2, array.shape[1] + border_width*2, array.shape[2]), np.uint8)
    border[border_width:border_width+array.shape[0], border_width:array.shape[1]+border_width, :] = array
    image = Image.fromarray(border)
    image = ImageTk.PhotoImage(image)
    return image

if __name__ == '__main__':
    root = tk.Tk()
    root.title("Code Generator")
    gui = GUI(master=root)
    gui.mainloop()