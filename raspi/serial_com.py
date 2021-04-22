import serial
import struct
from time import sleep
from gpiozero import LED
from image_info import get_image_info
from lib.config_reader import ConfigReader
from lib.cam import Camera

# Read the config file
config = ConfigReader()
print("Starting Camera")

# Define Hardware Pins
main_led = LED(int(config.param['hardware_parameters']['main_led_pin']))
flash = LED(int(config.param['hardware_parameters']['flash_pin']))
cam_led = LED(int(config.param['hardware_parameters']['cam_led_pin']))
serial_led = LED(int(config.param['hardware_parameters']['serial_led_pin']))

# Turn main LED on
main_led.on()

# Open camera
sleep(5)
cam = Camera(config.param['camera_parameters'])
cam.open()
cam_led.on()

# Open serial port
ser = serial.Serial()
ser.port = config.param['serial_parameters']['port']
ser.baudrate = int(config.param['serial_parameters']['baudrate'])
ser.open()
ser.reset_input_buffer()
ser.reset_output_buffer()
print("Serial openend")
serial_led.on()

def send_int_list(int_list):
    print(int_list)
    for i in int_list:
        b = struct.pack('B', i)
        ser.write(b)
    ser.write(b'\n')

# Endless loop listening for messages
while True:
    print("Waiting for message...")
    recv_data = b''

    # Read the bytes until a Return is hit
    while True:
        recv_byte = ser.read()
        if recv_byte == b'\r':
            break
        recv_data += recv_byte
    print("Message recieved!") 

    # Decode the bytes to string with UTF-8
    data_str = recv_data.decode()
    print("Message: " + data_str)
    
    # Send 'pong' if someone pings
    if data_str == 'ping':
        ser.write("pong".encode())
        ser.write(b'\n')

    # Take image, process it and send the info string
    elif data_str == 'shoot':
        cam_led.blink(0.3,0.3)
        image = cam.capture_image()
        info_list = get_image_info(image, config.param['image_parameters'], save_imgs=False)
        cam_led.on()
        send_int_list(info_list)

    # Take image, process it and send the info string
    elif data_str == 'save':
        cam_led.blink(0.3,0.3)
        image = cam.capture_image()
        info_list = get_image_info(image, config.param['image_parameters'], save_imgs=True)
        cam_led.on()
        send_int_list(info_list)

    # Turn Flash on and off
    elif data_str == 'flash':
        if flash.is_active:
            flash.off()
        else:
            flash.on()

    # Break the loop and terminate the program
    elif data_str == 'exit':
        break

    # Send N/A if command is not known
    else:
        ser.write("n/a".encode())
        ser.write(b'\n')

# Close the open interfaces
cam.close()
ser.close()

# Turn all LEDs off
main_led.off()
flash.off()
cam_led.off()
serial_led.off()