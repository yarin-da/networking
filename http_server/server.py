import socket
import sys
import os


# save recv data to tcp_buffer
# determine when a full message has arrived and return it
def receive_message(client, tcp_buffer):
    while True:
        # we have a full message in tcp_buffer if it contains the message delimiter
        buf_split = tcp_buffer.split('\r\n\r\n', 1)
        if len(buf_split) != 1:
            # return the message we found, and remove it from tcp_buffer
            tcp_buffer = buf_split[1]
            return buf_split[0]
        try:
            # read data from the socket into tcp_buffer in utf-8
            tcp_buffer += client.recv(BUFFER_SIZE).decode('utf-8')
        # notify caller when timeout/error occured with None
        except (socket.timeout, socket.error):
            return None


# take a message from the client and generate the appropriate response
# the function returns a tuple (connection, response, file_data)
# file_data may be None if we don't have a file to send
def handle_message(data):
    # default values
    connection = 'close'
    file_data = None
    response = ''
    length = 0

    # run line by line and search for the Connection line
    lines = data.splitlines()
    for line in lines:
        # if we found the line, update the connection variable
        if "Connection: " in line:
            connection = line.split(' ')[1]

    # first line is guaranteed to be GET
    filename = lines[0].split(' ')[1]
    # '/' refers to 'index.html'
    if filename == '/':
        filename = '/index.html'
    # return 301 response
    elif filename == '/redirect':
        response = 'HTTP/1.1 301 Moved Permanently\r\nConnection: close\r\nLocation: /result.html\r\n\r\n'
        return 'close', response, None
    
    filepath = 'files' + filename
    # if the path leads to nowhere, or to a folder then we return 404 response
    if not os.path.exists(filepath) or not os.path.isfile(filepath):
        response = 'HTTP/1.1 404 Not Found\r\nConnection: close\r\n\r\n'
        return 'close', response, None
    else:
        # determine the read mode required using the file's extension
        mode = 'r'
        if '.jpg' in filepath or '.ico' in filepath:
            mode = 'rb'
        with open(filepath, mode) as f:
            if mode == 'r':
                # convert the file to bytes
                file_data = bytes(f.read(), 'utf-8')
            else:
                # file is already read as a bytes object
                file_data = f.read()
        
        length = len(file_data)
        # return 200 OK
        response = f'HTTP/1.1 200 OK\r\nConnection: {connection}\r\nContent-Length: {length}\r\n\r\n'
        return connection, response, file_data


TCP_IP = '0.0.0.0'
TCP_PORT = int(sys.argv[1])
BUFFER_SIZE = 1024

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind((TCP_IP, TCP_PORT))
s.listen(1)

while True:
    client, addr = s.accept()
    # set socket timeout to 1 second
    client.settimeout(1)
    # initialize an empty buffer that holds all bytes received
    tcp_buffer = ''
    while True:
        message = receive_message(client, tcp_buffer)
        # if data is empty or None then we need to close the socket
        if not message: break
        print(message)
        # generate a response for the client and send it
        connection, response, file_data = handle_message(message)
        client.send(bytes(response, 'utf-8'))
        # send file_data if there's file data to be sent
        if file_data:
            client.send(file_data)
        # 'Connection: close' means we need to close the socket
        if connection == 'close': break
    client.close()

