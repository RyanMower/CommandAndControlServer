#!/usr/bin/env python3
import socket 
import os

## ========  Config  ========
HEADER = 64
FORMAT = 'utf-8'

## ========  Functions  ========
def snd_msg(conn, msg):
    message = msg.encode(FORMAT)
    length = str(len(message)).encode(FORMAT)
    length += b' ' * (HEADER - len(length))
    conn.send(length)
    conn.send(message)

def get_msg(conn):
    msg_length = conn.recv(HEADER).decode(FORMAT)
    if msg_length:
        msg_length = int(msg_length)
        msg = conn.recv(msg_length).decode(FORMAT)
        return msg 
    else:
        return ""
