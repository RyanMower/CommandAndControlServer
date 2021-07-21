#!/usr/bin/env python3
import socket 
import os
import tqdm
import sys

## ========  Config  ========
HEADER = 64
FORMAT = 'utf-8'
SEPARATOR = "<SEPARATOR>"
BUFFER_SIZE = 4096 # send 4096 bytes each time step

## ========  Functions  ========
def snd_msg(conn, msg):
    message = msg.encode(FORMAT)
    length = (str(len(message))).encode(FORMAT)
    length += b' ' * (HEADER - len(length))
    print("HEADER_LENGTH (64): " + str(len(length)))
    print(f'MSG_SIZE (2207): {str(len(message))}\n{msg}')
    conn.send(length)
    conn.send(message)

def get_msg(conn):
    msg_length = conn.recv(HEADER).decode(FORMAT)
    if msg_length:
        print("Recieved Length: " + str(msg_length))
        msg_length = int(msg_length)
        msg = conn.recv(msg_length).decode(FORMAT)
        print(f'OBTAINED_MSG:\n{msg}\n+++++++++++++++++++++++++++++++++++++')
        return msg
    else:
        return ""

def snd_file(conn, filename):
    try:
        filesize = os.path.getsize(filename)
    except:
        return f"{filename} does not exist."

    snd_msg(conn, f"{filename}{SEPARATOR}{filesize}")
    progress = tqdm.tqdm(range(filesize), f"Sending {filename}", unit="B", unit_scale=True, unit_divisor=1024)
    bytes_left = filesize

    with open(filename, 'rb') as f:
        while bytes_left > 0:
            # read the bytes from the file
            if bytes_left > BUFFER_SIZE:
                bytes_to_read = BUFFER_SIZE
            else:
                bytes_to_read = bytes_left
            bytes_read = f.read(bytes_to_read)
            bytes_left = bytes_left - bytes_to_read
            # we use sendall to assure transimission in
            # busy networks
            conn.sendall(bytes_read)
            # update the progress bar
            progress.update(len(bytes_read))
    progress.close()
    f.close()
    return "SUCCESS"

def get_file(conn):
    # receive the file infos
    # receive using client socket, not server socket
    received = get_msg(conn)
    filename, filesize = received.split(SEPARATOR)
 
    # convert to integer
    filesize = int(filesize)
 
    # start receiving the file from the socket
    # and writing to the file stream
    progress = tqdm.tqdm(range(filesize), f"Receiving {filename}.", unit="B", unit_scale=True, unit_divisor=1024)
    bytes_left = filesize
    with open(filename, "wb") as f:
        while bytes_left > 0:
            if bytes_left < BUFFER_SIZE:
                bytes_to_write = bytes_left
            else:
                bytes_to_write = BUFFER_SIZE
            # read 1024 bytes from the socket (receive)
            bytes_read = conn.recv(bytes_to_write)
            #print(bytes_read)
            bytes_left = bytes_left - bytes_to_write
            #print(f'Bytes left {str(bytes_left)}')
            # write to the file the bytes we just received
            f.write(bytes_read)
            # update the progress bar
            progress.update(len(bytes_read))
    progress.close()
    f.close()
    return "SUCCESS"

