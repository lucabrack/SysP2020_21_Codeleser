import socket


HOST = socket.gethostbyname('raspi')
PORT = 65432

print(HOST)

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HOST, PORT))
    text = input('What to send:')
    s.sendall(text.encode())
    data = s.recv(1024)

print('Received', data.decode())