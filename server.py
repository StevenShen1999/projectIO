# Sample code for Multi-Threaded Server
#Python 3
# Usage: python3 UDPserver3.py
#coding: utf-8
from socket import *
import threading
import time
import datetime as dt

from socket import *
from json import loads, dumps
#using the socket module

#Define connection (socket) parameters
#Address + Port no
#Server would be running on the same host as Client
# change this port number if required
serverPort = 12040

serverSocket = socket(AF_INET, SOCK_STREAM)

serverSocket.bind(('localhost', serverPort))

serverSocket.listen(1)

print("The server is ready to receive")

unsuccessful_logins = {}
logins = {}
with open("./credentials.txt", "r") as file:
    for i in file.readlines():
        i = i.strip().split(" ")
        logins[i[0]] = i[1]


while 1:
    try:
        connectionSocket, addr = serverSocket.accept()

        while 1:
            sentence = connectionSocket.recv(1024)
            sentence = loads(sentence)
            print(sentence)

            message = ""
            if (sentence['operation'] == 'login'):
                # First check if the account is currently locked out
                if (sentence['username'] in unsuccessful_logins):
                    print("Entered this bit")
                    if (not isinstance(unsuccessful_logins[sentence['username']], int)):
                        print("Entered here as well")
                        if (unsuccessful_logins[sentence['username']] > dt.datetime.now()):
                            message = "blocked_1"
                            break

                if (sentence['username'] not in logins):
                    message = ""
                else:
                    if (sentence['password'] == logins[sentence['username']]):
                        message = "logged_in"
                        # TODO: Remove this line when further features are implemented
                        # This currently crashes the server
                        break
                    else:
                        # TODO: Add a tally to this user's unsuccessful logins
                        # If it is three times lock
                        if (sentence['username'] in unsuccessful_logins):
                            unsuccessful_logins[sentence['username']] += 1
                            if (unsuccessful_logins[sentence['username']] == 3):
                                # TODO: Change this to block_time once we integrate the commandline
                                unsuccessful_logins[sentence['username']] = dt.datetime.now() + dt.timedelta(seconds=30)
                                message = "blocked_0"
                                break
                        else:
                            unsuccessful_logins[sentence['username']] = 1
                        message = "incorrect"
            elif (sentence['operation'] == 'logout'):
                break

            print(message)
            connectionSocket.send(dumps({"status": message}).encode('utf-8'))

        connectionSocket.send(dumps({"status": message}).encode('utf-8'))
        connectionSocket.close()
    except KeyboardInterrupt:
        serverSocket.close()
        print("Keyboard Interrupt: Server Closed")
        break