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

# import SSH libs
import paramiko
from scp import SCPClient

USER = 'pi'
PW = '1234'

IMG_SIZE = 500
SHAPE_SIZE = 15

class GUI(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.master = master
        self.pack()
        self.serial_answer = ''
        self.output_folder = ''
        self.code_img = array2image(np.ones((IMG_SIZE,IMG_SIZE,3), np.uint8)*255)
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
        
        self.button_generate = tk.Button(self, text="Code generieren",
                                         command=self.generate_code)
        self.button_generate.grid(row=2,column=3,columnspan=3)
        self.label_image = tk.Label(self,image=self.code_img)
        self.label_image.image = self.code_img
        self.label_image.grid(row=3,column=0,rowspan=1,columnspan=10)
        self.button_save = tk.Button(self, text="Code speichern",
                                     command=self.save_code)
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
        self.button_get_pics = tk.Button(self, text="Debug Bilder holen",
                                            command=self.get_pics)
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
            with serial.Serial(timeout=5.0) as ser:
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

                print("Waiting for Message...")
                recv_data = b''
                while True:
                    recv_byte = ser.read(size=1)
                    if recv_byte == b'\n': # Messsage fully recieved
                        print("Message recieved!")
                        if cmd != 'shoot' and cmd != 'save':
                            self.serial_answer = ''
                            self.entry_antwort.delete(0,len(self.entry_antwort.get()))
                            self.entry_antwort.insert(0, recv_data)
                        else:
                            self.serial_answer = struct.unpack('B'*len(recv_data), recv_data)
                            self.entry_antwort.delete(0,len(self.entry_antwort.get()))
                            self.entry_antwort.insert(0, self.serial_answer)
                        break
                    elif not recv_byte: # ser.read timed out
                        print("No Message recieved!")
                        self.serial_answer = ''
                        self.entry_antwort.delete(0,len(self.entry_antwort.get()))
                        self.entry_antwort.insert(0, "Keine Antwort erhalten! Überprüfe UART-Verbindung und COM-Port!")
                        break
                    recv_data += recv_byte
           
        except Exception as e:
            self.serial_answer = ''
            self.entry_antwort.delete(0,len(self.entry_antwort.get()))
            self.entry_antwort.insert(0, e)



    def generate_code(self):
        self.code_img = array2image(np.ones((IMG_SIZE,IMG_SIZE,3), np.uint8)*255)

        info_tuple = self.serial_answer
        if not info_tuple: pass
        
        # First 5 infos are for ROI
        shapes_tuple = info_tuple[5:]
        shapes_list = []

        # Group 3 entries together (shape form, x, y)
        tmp_l = []
        for i in range(len(shapes_tuple)):
            tmp_l.append(int(shapes_tuple[i]))
            if (i+1) % 3 == 0:
                shapes_list.append(tmp_l)
                tmp_l = []
        
        res_img = np.ones((IMG_SIZE,IMG_SIZE,3), np.uint8)*255
        for shape in shapes_list:
            x = int(shape[1]/255*IMG_SIZE)
            y = int(shape[2]/255*IMG_SIZE)

            if shape[0] == 0:
                res_img = draw_circle(res_img, (x,y))
            elif shape[0] == 1:
                res_img = draw_triangle(res_img, (x,y))
            elif shape[0] == 2:
                res_img = draw_rectangle(res_img, (x,y))
            elif shape[0] == 3:
                res_img = draw_cross(res_img, (x,y))

        self.code_img = array2image(res_img)
        self.label_image.configure(image=self.code_img)
        self.label_image.image = self.code_img

    def save_code(self):
        files = [('Image File', '*.png')]
        with filedialog.asksaveasfile(filetypes = files, defaultextension = files) as file:
            output_path = file.name
        self.code_img._PhotoImage__photo.write(output_path)
        print("Image saved!")

    def get_pics(self):
        try:
            ssh = paramiko.SSHClient()
            ssh.load_system_host_keys()
            ssh.connect(self.entry_ip.get(), username=self.entry_user.get(), password=self.entry_pw.get())
            
            output_folder = filedialog.askdirectory()
            if not output_folder: pass

            with SCPClient(ssh.get_transport()) as scp:
                scp.get('/home/pi/Projekte/SysP2020_21_Codeleser/raspi/debug', local_path=output_folder, recursive=True)
            print('Images copied successfully!')
            self.entry_error.delete(0,len(self.entry_error.get()))
            self.entry_error.insert(0, "Bilder erfolgreich kopiert nach: " + output_folder)

        except Exception as e:
            self.entry_error.delete(0,len(self.entry_error.get()))
            self.entry_error.insert(0, e)
        

def array2image(array):
    border_width = 20
    border = np.zeros((array.shape[0] + border_width*2, array.shape[1] + border_width*2, array.shape[2]), np.uint8)
    border[border_width:border_width+array.shape[0], border_width:array.shape[1]+border_width, :] = array
    image = Image.fromarray(border)
    image = ImageTk.PhotoImage(image)
    return image

def draw_circle(img, pos):
    cv2.circle(img, pos, SHAPE_SIZE, (0,0,0), -1)
    return img

def draw_rectangle(img, pos):
    x,y = pos
    top_left = (x-SHAPE_SIZE, y-SHAPE_SIZE)
    bottom_right = (x+SHAPE_SIZE, y+SHAPE_SIZE)
    cv2.rectangle(img, top_left, bottom_right, (0,0,0), -1)
    return img

def draw_triangle(img, pos):
    x,y = pos
    triangle_cnt = np.array([(x, y-SHAPE_SIZE) , (x-SHAPE_SIZE, y+SHAPE_SIZE), (x+SHAPE_SIZE, y+SHAPE_SIZE)])
    cv2.drawContours(img, [triangle_cnt], 0, (0,0,0), -1)
    return img

def draw_cross(img, pos):
    x,y = pos
    cross_cnt = np.array([(int(x+SHAPE_SIZE/4), y-SHAPE_SIZE), (int(x+SHAPE_SIZE/4), int(y-SHAPE_SIZE/4)),
                 (x+SHAPE_SIZE, int(y-SHAPE_SIZE/4)), (x+SHAPE_SIZE, int(y+SHAPE_SIZE/4)),
                 (int(x+SHAPE_SIZE/4), int(y+SHAPE_SIZE/4)), (int(x+SHAPE_SIZE/4), y+SHAPE_SIZE),
                 (int(x-SHAPE_SIZE/4), y+SHAPE_SIZE), (int(x-SHAPE_SIZE/4), int(y+SHAPE_SIZE/4)),
                 (x-SHAPE_SIZE, int(y+SHAPE_SIZE/4)), (x-SHAPE_SIZE, int(y-SHAPE_SIZE/4)),
                 (int(x-SHAPE_SIZE/4), int(y-SHAPE_SIZE/4)), (int(x-SHAPE_SIZE/4), y-SHAPE_SIZE)])
    cv2.drawContours(img, [cross_cnt], 0, (0,0,0), -1)
    return img

if __name__ == '__main__':
    root = tk.Tk()
    root.title("Code Generator")
    gui = GUI(master=root)
    gui.mainloop()