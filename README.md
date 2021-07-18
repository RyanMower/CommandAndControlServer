# CommandAndControlServer
CommandAndControlServer is a basic command and control server used for post exploitation. After compromising a victim, run `client.py` on the victim's machine and have it connect back to the main `server.py`. The server is able to:
1. broadcast <cmd here>
2. list
3. send <ip> <cmd here>
4. put <filename> <ip>
5. grab <filename> <ip>
6. close <ip>
7. help

The `ip` and `port` number can be configured in the configuration heading in each of the scripts. 
