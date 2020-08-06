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

#Server would be running on the same host as Client
serverName = sys.argv[1]
serverPort = int(sys.argv[2])
clientUDPport = int(sys.argv[3])

# UDP Connections
clientSocket_p2p = socket(AF_INET, SOCK_DGRAM)
serverSocket = socket(AF_INET, SOCK_DGRAM)
serverSocket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
serverSocket.bind(('localhost', clientUDPport)) 

# TCP Connection
clientSocket = socket(AF_INET, SOCK_STREAM)
clientSocket.connect((serverName, serverPort))

''' Don't need to touch this again, this is the initial login logic '''
username = input("Username: ")
password = input("Password: ")

initial_payload = {"operation": "login", "username": username, "password": password}
clientSocket.send(dumps(initial_payload).encode('utf-8'))
valid_commands = {"Download_tempID", "logout", "Upload_contact_log"}
logged_out = False
tempID = {'id': '0000000', 'start': '000000', 'end': '000000'}

# TODO: With time, refactor these error message codes and statuses into integers
def tcp_handler():
    global clientSocket
    global valid_commands
    global logged_out
    global tempID
    previous_command_p2p = False

    while(1):
        # TCP Server/client traffic
        if not previous_command_p2p:
            message = clientSocket.recv(2048)
            print(message)
            message = loads(message)
            local_payload = {}

            if (message['status'] == ""):
                print("Something else went wrong")
                logged_out = True
                break
            elif (message['status'] == "incorrect"):
                print("Invalid Password. Please try again")
                password = input("Password: ")

                local_payload = {"operation": "login", "username": username, "password": password}
                clientSocket.send(dumps(local_payload).encode('utf-8'))
                continue
            elif (message['status'] == "blocked_0"):
                print("Invalid Password. Your account has been blocked. Please try again later")
                break
            elif (message['status'] == "blocked_1"):
                print("Your account is blocked due to multiple login failures. Please try again later")
                break
            elif (message['status'] == "logged_in"):
                print("Welcome to the BlueTrace Simulator!")
            elif (message['status'] == "logged_out"):
                logged_out = True
                break
            elif (message['status'] == "success"):
                if ('id' in message):
                    print(f"TempID: {message['id']}")
                    # Storing this for the beacon
                    curr_time = dt.datetime.now()
                    tempID['id'] = message['id']
                    tempID['start'] = curr_time.strftime("%d/%m/%Y %H:%M:%S")
                    tempID['end'] = (curr_time + dt.timedelta(minutes=3)).strftime("%d/%m/%Y %H:%M:%S")

        previous_command_p2p = False

        command = input("")
        while (command not in valid_commands and command.find("Beacon") == -1):
            print("Error. Invalid command")
            command = input("")

        local_payload = {"operation": command}

        if (command == "Upload_contact_log"):
            # TODO: Change this to the actual contact log (depending on how p2p is implemented)
            with open("./z5161616_contactlog.txt") as file:
                contacts = file.readlines()
                # Read in all the contacts
                contacts = [i.strip().split(" ") for i in contacts]
                for i in contacts:
                    print(f"{i[0]}, {i[1]} {i[2]}, {i[3]} {i[4]};")

                local_payload["payload"] = contacts
        elif (command.find("Beacon") != -1):
            # First parse the information
            command = command.split(" ")
            if (len(command) != 3):
                # TODO: Handle the situation where this send beacon command doesn't have the right syntax
                pass

            p2p_sender(command[1], int(command[2]), tempID)
            previous_command_p2p = True
            continue

        print(local_payload)
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

        try:
            start = dt.datetime.strptime(p2p_message['start'], "%d/%m/%Y %H:%M:%S") 
            end =  dt.datetime.strptime(p2p_message['end'], "%d/%m/%Y %H:%M:%S")

            if (start <= current_time <= end):
                # valid time stamp, write to the contact log
                invalid = False
        except ValueError as e:
            continue


        print(f"received beacon: {p2p_message['id']}, {p2p_message['start']}, {p2p_message['end']}.")
        print(f"Current time is: {current_time}.")
        print(f"The beacon is {'invalid' if invalid else 'valid'}.")

        if not invalid:
            with open("./z5161616_contactlog.txt", "a") as file:
                file.writelines(f"{p2p_message['id']} {p2p_message['start']} {p2p_message['end']}\n")

# This gets initialised in the tcP_handler function, we only initialise this after the client log in
# and wants to send a beacon to someone
def p2p_sender(address, port, payload):
    global serverSocket
    global clientSocket_p2p

    # Send the tempID, the two timestamps to the target address/port
    clientSocket_p2p.sendto(dumps(payload).encode(), (address, port,))

    # TODO: Handle the case when the sending was not successful


# TODO: Add a function here that reads the contactlog every 1 min and remove beacons older than 3 mins
# use the threading module to achieve this

def main():
    start_new_thread(tcp_handler, ())
    start_new_thread(p2p_receiver, ())

    while 1:
        if (logged_out):
            print("Entered here")
            break
        sleep(0.1)

    serverSocket.close()

if __name__ == "__main__":
    main()