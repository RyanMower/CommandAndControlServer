#!/usr/bin/env python3
import socket 
import threading

## ========  Config  ========
HEADER = 64
PORT = 5052
#SERVER = '10.96.10.191'
SERVER = socket.gethostbyname(socket.gethostname())
ADDR = (SERVER, PORT)
FORMAT = 'utf-8'
DISCONNECT_MESSAGE = "exit"


## ========  Globals  ========
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(ADDR)
connected_machines = []

## ========  Functions  ========
def handle_client(conn, addr):
    #conn.send(f"Connected to {SERVER}".encode(FORMAT))
    connected = True
    while connected:
        msg_length = conn.recv(HEADER).decode(FORMAT)
        if msg_length:
            msg_length = int(msg_length)
            msg = conn.recv(msg_length).decode(FORMAT)
            if msg == DISCONNECT_MESSAGE:
                connected = False

            print(f"[{addr}] {msg}")
            conn.send("Msg received".encode(FORMAT))

    conn.close()
       
# Processes the user input
def handle_user():

    while True:
        cmd = input("> ") 
        cmd_lst = cmd.split()
        if len(cmd_lst) <= 0:
            continue

        ## Broadcast
        elif cmd_lst[0] == "broadcast":
            new_cmd = ' '.join(cmd_lst[1:])
            print(f'Sending \"{new_cmd}\" to...')
            for data in connected_machines:
                print(data['addr'][0])
                new_cmd = ' '.join(cmd_lst[1:])
                data['conn'].send(new_cmd.encode(FORMAT))

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
                    break
            if not sent:
                print(f'{new_cmd[0]} is not connected to the server.')

        ## help
        elif cmd_lst[0] == "help":
            print("1. broadcast <cmd here>")
            print("2. list")
            print("3. send <ip> <cmd here>")
            print("4. help")

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
        thread = threading.Thread(target=handle_client, args=(conn, addr))
        thread.start()


start()
