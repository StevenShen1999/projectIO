# Python 3.6.9
# coding: utf-8
# Skeleton code from webcms3's COMP3331 assignment page

from socket import AF_INET, SOCK_DGRAM, SOCK_STREAM, SO_REUSEADDR, SOL_SOCKET, socket
import sys
from json import loads, dumps
from time import sleep
from threading import *
from _thread import start_new_thread
import datetime as dt
import sys

if len(sys.argv) != 4:
    print("Usage: python3 client.py server_ip server_port client_udp_port")
    exit(0)

# For when the automatic scrubber removes outdated beacons
file_lock = Lock()

#Server would be running on the same host as Client
serverName = sys.argv[1]
serverPort = int(sys.argv[2])
clientUDPport = int(sys.argv[3])

# UDP Connections
clientSocket_p2p = socket(AF_INET, SOCK_DGRAM)
serverSocket = socket(AF_INET, SOCK_DGRAM)
serverSocket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)

# Assuming that the server is running on the server IP as the client
serverSocket.bind((serverName, clientUDPport)) 

# TCP Connection
clientSocket = socket(AF_INET, SOCK_STREAM)
clientSocket.connect((serverName, serverPort))

# No matter what, we always ask for the login details when spinning up a client instance
username = input("Username: ")
password = input("Password: ")

# Login this current client (or at least attempt to)
initial_payload = {"operation": "login", "username": username, "password": password}
clientSocket.send(dumps(initial_payload).encode('utf-8'))

# Some global variables to help with the TCP logic later
valid_commands = {"Download_tempID", "logout", "Upload_contact_log"}

# To exit the client
logged_out = False

# To store the tempID downloaded from the server, otherwise, a dict of 0s
tempID = {'id': '0000000', 'start': '000000', 'end': '000000', 'protocol': '1'}
statuses = {
    "blocked_0": "Invalid Password. Your account has been blocked. Please try again later",
    "blocked_1": "Your account is blocked due to multiple login failures. Please try again later",
    "Not a valid user": "Account does not exist",
    "logged_out": None
}

# Three functions in this client.py logic

# This function handles the TCP connections
def tcp_handler():
    global clientSocket
    global valid_commands
    global logged_out
    global tempID

    # A special case, since for p2p connections, no responses will be observed
    previous_command_p2p = False

    while(1):
        # TCP Server/client traffic
        # If the previous command was a p2p command (i.e. Beacon), we skip over the TCP logic
        if not previous_command_p2p:
            # Receive the server responses
            message = clientSocket.recv(2048)

            # Serialise response into python object
            message = loads(message)
            local_payload = {}

            # Handle the various messages
            if (message['status'] in statuses):
                if (statuses[message['status']]):
                    print(statuses[message['status']])
                logged_out = True
                break

            # Incorrect password logic, note that if this user is blocked, it will enter the condition above
            # and exit this client
            elif (message['status'] == "incorrect"):
                print("Invalid Password. Please try again")
                password = input("Password: ")

                local_payload = {"operation": "login", "username": username, "password": password}
                clientSocket.send(dumps(local_payload).encode('utf-8'))
                continue

            # We are logged in, can start listening to commands from the client
            elif (message['status'] == "logged_in"):
                print("Welcome to the BlueTrace Simulator!")

            # THis is the case when the tempID is successfully generated and returned to the client
            elif (message['status'] == "success"):
                print(f"TempID: {message['id']}")

                # Storing this tempID for the p2p beacon information
                curr_time = dt.datetime.now()
                tempID['id'] = message['id']
                tempID['start'] = curr_time.strftime("%d/%m/%Y %H:%M:%S")
                tempID['end'] = (curr_time + dt.timedelta(minutes=3)).strftime("%d/%m/%Y %H:%M:%S")

            # This is the case when the upload contact log was successful
            elif (message['status'] == "success_1"):
                # No printout required
                pass

        # Reset this variable
        previous_command_p2p = False

        command = input("> ")
        # We keep on repeating this input() until the user inputs a valid command
        while (command not in valid_commands):
            if (command.find("Beacon") != -1):
                command = command.split(" ")
                if (len(command) != 3):
                    print("Error, usage: Beacon targetIP targetPort")
                else:
                    break
            else:
                print("Error. Invalid command")
            command = input("> ")

        # We can most likely improve the performance using say integer flags, but I ran out of time :(
        local_payload = {"operation": command}

        if (command == "Upload_contact_log"):
            # Need to extract the information from the contactlog file
            with open("./z5161616_contactlog.txt") as file:
                contacts = file.readlines()

                # Read in all the contacts, and do some preprocessing, i.e. remove trailing \n 
                contacts = [i.strip().split(" ") for i in contacts]

                for i in contacts:
                    print(f"{i[0]}, {i[1]} {i[2]}, {i[3]} {i[4]};")

                # Attach the list to the payload
                local_payload["payload"] = contacts

        # This means we are using a p2p command
        elif (command[0] == "Beacon"):
            previous_command_p2p = True

            # Send the specified address + port combo this particular beacon information
            clientSocket_p2p.sendto(dumps(tempID).encode(), (command[1], int(command[2]),))
            continue

        clientSocket.send(dumps(local_payload).encode('utf-8'))

    clientSocket.close()

def p2p_receiver():
    global serverSocket

    while 1:
        # UDP p2p traffic, receive a message and gather client address
        p2p_message, clientAddress = serverSocket.recvfrom(2048)

        # Decode the message (beacon)
        p2p_message = loads(p2p_message.decode())
        invalid = True
        current_time = dt.datetime.now()

        # Attempt to decode the message sent 
        try:
            start = dt.datetime.strptime(p2p_message['start'], "%d/%m/%Y %H:%M:%S") 
            start -= dt.timedelta(microseconds=start.microsecond)
            end = dt.datetime.strptime(p2p_message['end'], "%d/%m/%Y %H:%M:%S")
            end -= dt.timedelta(microseconds=end.microsecond)

            if (start <= current_time <= end):
                # valid time stamp, write to the contact log
                invalid = False
        except ValueError as e:
            start = p2p_message['start']
            end = p2p_message['end']


        print(f"received beacon: {p2p_message['id']}, {p2p_message['start']}, {p2p_message['end']}.")
        print(f"Current time is: {current_time}.")
        print(f"The beacon is {'invalid' if invalid else 'valid'}.")

        if not invalid:
            with open("./z5161616_contactlog.txt", "a") as file:
                file.writelines(f"{p2p_message['id']} {p2p_message['start']} {p2p_message['end']}\n")


# This function wakes up every 30 seconds to remove contact log beacons older than 3 minutes
def contact_log_scrubber():
    while 1:
        file_lock.acquire()
        with open("./z5161616_contactlog.txt", "r") as file:
            contacts = file.readlines()
            contacts = [i.strip().split(" ") for i in contacts]
            contacts = [i for i in contacts if (dt.datetime.strptime(i[1] + " " + i[2], "%d/%m/%Y %H:%M:%S") + dt.timedelta(minutes=3) > dt.datetime.now())]

        with open("./z5161616_contactlog.txt", "w") as file:
            for i in contacts:
                file.writelines(' '.join(i) + "\n")

        file_lock.release()

        sleep(30)

def main():
    start_new_thread(tcp_handler, ())
    start_new_thread(p2p_receiver, ())
    start_new_thread(contact_log_scrubber, ())

    while 1:
        if (logged_out):
            break
        sleep(0.1)

    serverSocket.close()

if __name__ == "__main__":
    main()