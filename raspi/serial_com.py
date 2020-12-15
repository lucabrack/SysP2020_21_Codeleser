import serial
from time import sleep
from image_info import get_image_info
from lib.image_processing import open_camera
from lib.config_reader import ConfigReader

ser = serial.Serial("/dev/ttyS0", 9600)
print("Serial openend")

while True:
    print("Waiting for message...")
    recv_data = b''
    while True:
        recv_byte = ser.read()
        if recv_byte == b'\r':
            break
        recv_data += recv_byte
        sleep(0.03)
    print("Message recieved!") 

    data_str = recv_data.decode()
    if 
    
    print(recv_data.decode())
    ser.write(recv_data)