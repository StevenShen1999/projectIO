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

import sys

if len(sys.argv) != 3:
    print("Usage: python3 server.py server_port block_duration")

# Initialising some global variables
unsuccessful_logins = {}
logins = {}
file_lock = threading.Lock()
block_duration = int(sys.argv[2])

# Load in the credentials.txt file
# Since we don't have to create new accounts, just need to read in credentials once
with open("./credentials.txt", "r") as file:
    for i in file.readlines():
        i = i.strip().split(" ")
        logins[i[0]] = i[1]

def threaded_client(connectionSocket):
    # The client that this particular thread is servicing
    local_user = None

    global unsuccessful_logins
    global logins

    while True:
        sentence = connectionSocket.recv(1024)

        sentence = loads(sentence)

        message = ""
        payload = None
        if (sentence['operation'] == 'login'):
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
                message = "Not a valid user"
            else:
                # Check the passwords against the stored login information
                if (sentence['password'] == logins[sentence['username']]):
                    message = "logged_in"
                    local_user = sentence['username']
                else:
                    if (sentence['username'] in unsuccessful_logins):
                        unsuccessful_logins[sentence['username']] += 1
                        # Lock the account if this is the third time the user has inputted a wrong password
                        if (unsuccessful_logins[sentence['username']] == 3):
                            # Set a locked until time
                            unsuccessful_logins[sentence['username']] = dt.datetime.now() + dt.timedelta(seconds=block_duration)
                            message = "blocked_0"
                            break
                    else:
                        unsuccessful_logins[sentence['username']] = 1
                    message = "incorrect"
        elif (sentence['operation'] == 'logout'):
            message = "logged_out"
            print(f"> {local_user} logout")
            break
        elif (sentence['operation'] == 'Download_tempID'):
            print(f"> user: {local_user}")
            file_lock.acquire()

            # Generate a random 20 bytes ascii string
            temp_id = ''.join(choices(ascii_lowercase+ascii_uppercase+digits, k=20))

            # Write to the temPID logfile the tempID generated time and also expiry time
            current_time = dt.datetime.now()
            current_time = current_time.strftime("%d/%m/%Y %H:%M:%S")
            expiry_time = dt.datetime.now() + dt.timedelta(minutes=15)
            expiry_time = expiry_time.strftime("%d/%m/%Y %H:%M:%S")

            # Write to the file
            with open("./tempIDs.txt", "a") as file:
                file.writelines(f"{local_user} {temp_id} {current_time} {expiry_time}\n")

            file_lock.release()

            message = "success"
            print(f"> TempID: {temp_id}")
            payload = {"id": temp_id}

        elif (sentence['operation'] == 'Upload_contact_log'):
            # Retrieve the contact log
            contacts_to_check = {}
            print(f"> received contact log from {local_user}")

            for i in sentence['payload']:
                # Go through the payload and convert the uploaded contacg log to native python datetime objects
                print(f"{i[0]}, {i[1]} {i[2]}, {i[3]} {i[4]};")
                contacts_to_check[i[0]] = {}
                contacts_to_check[i[0]]['start'] = dt.datetime.strptime(i[1] + " " + i[2], "%d/%m/%Y %H:%M:%S")
                contacts_to_check[i[0]]['end'] = dt.datetime.strptime(i[3] + " " + i[4], "%d/%m/%Y %H:%M:%S")

            # Trace
            print("> Contact log checking")

            file_lock.acquire()
            # First get a list of all the tempIDs
            with open("./tempIDs.txt", "r") as file:
                tempIDs = file.readlines()

                # Some preprocessing to remove the trailing \n and also split the string
                tempIDs = [i.strip().split(" ") for i in tempIDs]
                for i in tempIDs:
                    temp_id = i[1]

                    # Convert the stored timestamps in the txt file into native python datetime objects
                    time = dt.datetime.strptime(i[2] + " " + i[3], "%d/%m/%Y %H:%M:%S")

                    # Check if this particular tempID needs to be checked
                    if (temp_id in contacts_to_check):

                        # Verify the timestamp validity
                        if (contacts_to_check[temp_id]['start'] <= time <= contacts_to_check[temp_id]['end']):
                            print(f"{i[0]}, {contacts_to_check[temp_id]['start']};")

            file_lock.release()

            numbers = {}
            message = "success_1"

        # Serve server responses back to the client
        if (not payload):
            connectionSocket.send(dumps({"status": message}).encode())
        else:
            payload["status"] = message
            connectionSocket.send(dumps(payload).encode())
        

    # This gets reached either by error states (i.e. locked out by three incomplete passwords, lock out time not reached)
    connectionSocket.send(dumps({"status": message}).encode())
    connectionSocket.close()

def main():
    serverPort = int(sys.argv[1])

    serverSocket = socket(AF_INET, SOCK_STREAM)

    serverSocket.bind(('localhost', serverPort))

    serverSocket.listen(1)

    # The server will spin up a new thread for each incoming connection, allowing for multiple clients
    # to access the server concurrently
    while 1:
        connectionSocket, addr = serverSocket.accept()
        start_new_thread(threaded_client, (connectionSocket,))

    serverSocket.close()

if __name__ == "__main__":
    main()