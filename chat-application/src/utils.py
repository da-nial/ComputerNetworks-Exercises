import os
import random
import sqlite3
import sys
from time import sleep

import tqdm


def generate_name(file_path='usernames.txt'):
    """"
    Chooses a random line from the given file, deletes that line, and the returns it.
    Notice this function uses an algorithm with O(n**2) complexity which could be slow.
    """
    with open(file_path, 'r') as f:
        usernames = f.read().splitlines()
        # print(usernames)
        chosen_index = random.choice(range(len(usernames)))
        chosen_username = usernames[chosen_index]

    usernames.remove(chosen_username)

    with open(file_path, 'w') as f:
        f.writelines(username + "\n"
                     for username in usernames)

    return chosen_username


def db_connection(db_file):
    """ create a database connection to the SQLite database
        specified by db_file
    :param db_file: database file
    :return: Connection object or None
    """
    conn = None
    try:
        conn = sqlite3.connect(db_file, check_same_thread=False)
    except Exception as e:
        print(e)

    return conn


def pack_message(sender, recipient, content):
    return ("From: {}|To: {}|Content: {}".format(sender, recipient, content)).encode('ascii')


def unpack_message(message):
    try:
        message = message.decode('ascii')
        sender, recipient, content = message.split('|')
        sender = sender.lstrip('From: ')
        recipient = recipient.lstrip('To: ')
        content = content.lstrip('Content: ')
        return sender, recipient, content
    except ValueError:
        print('An Exception in unpack')
        print(message)


def send_file(sock, filepath, filesize, BUFFER_SIZE=1024):
    # start sending the file
    progress = tqdm.tqdm(range(filesize), f"Sending {filepath}", unit="B",
                         unit_scale=True, unit_divisor=1024, file=sys.stdout)

    sock.settimeout(5.0)
    try:
        with open(filepath, "rb") as f:
            # Start receiving data until the whole file is received
            bytes_sent = 0
            while bytes_sent < filesize:
                sleep(0.1)
                data = f.read(BUFFER_SIZE)
                sock.sendall(data)
                bytes_sent += len(data)
                progress.update(len(data))

            sys.stdout.flush()
            f.close()
    except:
        print("Possible Connection Timeout!")

    sock.settimeout(None)


def recv_file(sock, filename, filesize, save_dir, BUFFER_SIZE=1024):
    save_path = os.path.join(save_dir, filename)
    print(save_path)

    # start receiving the file from the socket and writing to the file stream
    progress = tqdm.tqdm(range(filesize), f"Receiving {filename}", unit="B",
                         unit_scale=True, unit_divisor=1024, file=sys.stdout)

    # try:
    with open(save_path, "wb") as f:
        # Start receiving data until the whole file is received
        bytes_received = 0
        while bytes_received < filesize:
            data = sock.recv(BUFFER_SIZE)
            f.write(data)
            bytes_received += len(data)
            progress.update(len(data))

        sys.stdout.flush()
        f.close()
