#!/usr/bin/env python3
import socket 
import os

## ========  Functions  ========
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
