#Python 3
#Usage: python3 UDPClient3.py localhost 12000
#coding: utf-8
#Skeleton code from webcms3's COMP3331 assignment page
from socket import *
import sys
from json import loads, dumps
from time import sleep

#Server would be running on the same host as Client
serverName = sys.argv[1]
serverPort = int(sys.argv[2])

# TCP Connection
clientSocket = socket(AF_INET, SOCK_STREAM)
clientSocket.connect((serverName, serverPort))

''' Don't need to touch this again, this is the initial login logic '''
username = input("Username: ")
password = input("Password: ")

initial_payload = {"operation": "login", "username": username, "password": password}
clientSocket.send(dumps(initial_payload).encode('utf-8'))
valid_commands = {"Download_tempID", "logout", "Upload_contact_log"}

# TODO: With time, refactor these error message codes and statuses into integers
while(1):
    message = clientSocket.recv(2048)
    print(message)
    message = loads(message)
    local_payload = {}

    if (message['status'] == ""):
        print("Something else went wrong")
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
        # TODO: Change this to allow sending additional payloads once we get the other features online
    elif (message['status'] == "logged_out"):
        break
    elif (message['status'] == "success"):
        if ('id' in message):
            print(f"TempID: {message['id']}")

    command = input("")
    while (command not in valid_commands):
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

    print(local_payload)
    clientSocket.send(dumps(local_payload).encode('utf-8'))



clientSocket.close()