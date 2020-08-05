# Sample code for Multi-Threaded Server
#Python 3
# Usage: python3 UDPserver3.py
#coding: utf-8
from socket import *
import threading
from _thread import start_new_thread
import time
import datetime as dt

from socket import *
from json import loads, dumps
from random import choices
from string import ascii_lowercase, ascii_uppercase, digits

unsuccessful_logins = {}
logins = {}
file_lock = threading.Lock()

# Load in the credentials.txt file
with open("./credentials.txt", "r") as file:
    for i in file.readlines():
        i = i.strip().split(" ")
        logins[i[0]] = i[1]

def threaded_client(connectionSocket):
    local_user = None
    global unsuccessful_logins
    global logins
    while True:
        sentence = connectionSocket.recv(1024)

        sentence = loads(sentence)
        print(sentence)

        message = ""
        payload = None
        if (sentence['operation'] == 'login'):
            print("Entered this bit")
            # First check if the account is currently locked out
            if (sentence['username'] in unsuccessful_logins):
                if (not isinstance(unsuccessful_logins[sentence['username']], int)):
                    if (unsuccessful_logins[sentence['username']] > dt.datetime.now()):
                        message = "blocked_1"
                        break
                    else:
                        # This occurrs when the blacklist time has expired
                        # Thus allow login to recommence
                        unsuccessful_logins.pop(sentence['username'])

            if (sentence['username'] not in logins):
                message = ""
            else:
                if (sentence['password'] == logins[sentence['username']]):
                    message = "logged_in"
                    local_user = sentence['username']
                else:
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
            message = "logged_out"
            break
        elif (sentence['operation'] == 'Download_tempID'):
            file_lock.acquire()
            temp_id = ''.join(choices(ascii_lowercase+ascii_uppercase+digits, k=20))
            current_time = dt.datetime.now()
            current_time = current_time.strftime("%d/%m/%Y %H:%M:%S")
            expiry_time = dt.datetime.now() + dt.timedelta(minutes=15)
            expiry_time = expiry_time.strftime("%d/%m/%Y %H:%M:%S")

            with open("./tempIDs.txt", "a") as file:
                file.writelines(f"{local_user} {temp_id} {current_time} {expiry_time}\n")
            file_lock.release()
            message = "success"
            payload = {"id": temp_id}
        elif (sentence['operation'] == 'Upload_contact_log'):
            # FIXME: Have I got the contacts_to_check and tempIDs the other way around?

            # Retrieve the contact log
            contacts_to_check = {}
            print(f"received contact log from {local_user}")
            for i in sentence['payload']:
                print(f"{i[0]}, {i[1]} {i[2]}, {i[3]} {i[4]};")
                contacts_to_check[i[0]] = {}
                print(i[1] + " " + i[2])
                contacts_to_check[i[0]]['start'] = dt.datetime.strptime(i[1] + " " + i[2], "%d/%m/%Y %H:%M:%S")
                contacts_to_check[i[0]]['end'] = dt.datetime.strptime(i[3] + " " + i[4], "%d/%m/%Y %H:%M:%S")

            # Trace
            print("Contact log checking")

            # First get a list of all the tempIDs
            file_lock.acquire()
            with open("./tempIDs.txt", "r") as file:
                tempIDs = file.readlines()
                tempIDs = [i.strip().split(" ") for i in tempIDs]
                for i in tempIDs:
                    temp_id = i[1]
                    time = dt.datetime.strptime(i[2] + " " + i[3], "%d/%m/%Y %H:%M:%S")

                    # I don't know if we need to check the alternative (i.e. the temp_id in the contactlog is fake)
                    if (temp_id in contacts_to_check):
                        if (contacts_to_check[temp_id]['start'] <= time <= contacts_to_check[temp_id]['end']):
                            print(f"{i[0]}, {contacts_to_check[temp_id]['start']};")

            file_lock.release()

            numbers = {}
            for i in sentence['payload']:
                print(i)
            message = "success"

        if (not payload):
            connectionSocket.send(dumps({"status": message}).encode('utf-8'))
        else:
            payload["status"] = message
            connectionSocket.send(dumps(payload).encode('utf-8'))
        

    # This gets reached either by error states (i.e. locked out by three incomplete passwords, lock out time not reached)
    connectionSocket.send(dumps({"status": message}).encode('utf-8'))
    connectionSocket.close()

        

#Define connection (socket) parameters
#Address + Port no
#Server would be running on the same host as Client
# change this port number if required

def main():
    # TODO: Change this to dynamic
    serverPort = 12006

    serverSocket = socket(AF_INET, SOCK_STREAM)

    serverSocket.bind(('localhost', serverPort))

    serverSocket.listen(1)

    print("The server is ready to receive")

    while 1:
        connectionSocket, addr = serverSocket.accept()
        start_new_thread(threaded_client, (connectionSocket,))

    serverSocket.close()

if __name__ == "__main__":
    main()