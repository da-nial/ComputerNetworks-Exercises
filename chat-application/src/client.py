import argparse
import os
import socket
import threading

from .utils import pack_message, unpack_message, send_file, recv_file

BUFFER_SIZE = 1024 * 4  # 4KB


class Send(threading.Thread):
    def __init__(self, sock):
        super().__init__()
        self.sock = sock
        self.name = 'UNK'
        self.recipient = 'broadcast'

    def run(self):
        while True:
            input_str = input('{}: '.format(self.name))

            # Type '/quit' to leave the chatroom
            if input_str == '/quit':
                self.sock.sendall('Server: {} has left the chat.'.format(self.name).encode('ascii'))
                break

            elif input_str.startswith('/send-file'):
                _, filepath = input_str.split()

                filesize = int(os.path.getsize(filepath))
                filename = os.path.basename(filepath)

                content = '/send-file {} {}'.format(filename, filesize)

                # send the filename and filesize
                message = pack_message(self.name, self.recipient, content)
                self.sock.sendall(message)

                send_file(self.sock, filepath, filesize)

            # Send message (or command) to server_media
            else:
                message = pack_message(self.name, self.recipient, content=input_str)
                self.sock.sendall(message)

        print('\nQuiting...')
        self.sock.close()
        os._exit(0)


class Receive(threading.Thread):
    def __init__(self, sender, sock, save_dir):
        super().__init__()
        self.sender = sender
        self.sock = sock
        self.name = 'UNK'
        self.save_dir = save_dir

    def run(self):
        while True:
            message = self.sock.recv(1024)
            if message:
                self.parse(message)
                # print('\r{}\n{}: '.format(message.decode('ascii'), self.name), end='')
            else:
                # Server has closed the socket, exit the program
                print('\nOh no, we have lost connection to the Server!')
                print('\nQuitting...')
                self.sock.close()
                os._exit(0)

    def parse(self, message):
        """ Parse the received data, print out the messages, execute the commands.
        :param message:
        :return:
        """
        print()
        sender, recipient, content = unpack_message(message)

        if content.startswith('INIT_USERNAME'):
            _, new_username = content.split('=')
            self.name = new_username
            self.sender.name = new_username
            print('\nYour Username is: ' + new_username)
            print("If you don't like it, you can always change it by typing the command `/change-username`!\n")

            content = '{} has joined the chat. Say hi!'.format(self.name)
            message = pack_message('Server', 'broadcast', content)
            self.sock.sendall(message)

        elif content.startswith("/"):
            if content.startswith("/send-file"):
                _, filename, filesize = content.split()
                filesize = int(filesize)
                recv_file(self.sock, filename, filesize, self.save_dir)

            elif content.startswith("/change-chat_result"):
                _, new_recipient = content.split('=')
                if new_recipient != '-1':
                    self.sender.recipient = new_recipient
                    print("You are now chatting with " + new_recipient)
                else:
                    print("It seems like this user is not currently online!")

            elif content.startswith("/change-username_result"):
                _, new_username = content.split('=')
                if new_username != '-1':
                    self.name = new_username
                    self.sender.name = new_username
                    print("Your username successfully changed to: {}".format(new_username))
                else:
                    print("Sorry! It seems like this one is already taken!")

            elif content.startswith("/online-users"):
                online_users = content.split('\n')
                print('Following Users are currently online')
                for i, user in enumerate(online_users[1:]):
                    print('#{}.\t{}'.format(i, user))
                print('\nYou can chat with each one by typing the command change-chat')

            elif content.startswith("/create-group_result"):
                _, new_created_group = content.split('=')
                if new_created_group == '-1':
                    print("Group creation failed! This name is either not vaild or taken!")
                else:
                    print("Group created successfully!")

            elif content.startswith("/join-group_result"):
                _, new_joined_group = content.split('=')
                if new_joined_group == '-1':
                    print("No Such Group Found!")
                elif new_joined_group == '0':
                    print("You've already joined this group!")
                    print("To chat with them, simply use command `/change-chat {}`")
                else:
                    print("Yay! You are now a member of group {}".format(new_joined_group))
                    print("To chat with them, simply type `/change-chat {}`".format(new_joined_group))

            elif content.startswith("/show-groups_result"):
                _, available_groups = content.split('=')
                print(' #\tName\tCreator Address\t\tCreation Date')
                print(available_groups)
                print("To chat with anyone of them, enter command `change-chat`")

            elif content.startswith("/leave-group_result"):
                _, new_left_group = content.split('=')
                if new_left_group == '-1':
                    print("No Such Group Found!")
                elif new_left_group == '0':
                    print("You were not a member of this group!")
                else:
                    print("You Successfully left the group {}".format(new_left_group))
                    print("You can always come back by using command `/join-group {}`".format(new_left_group))

            elif content.startswith("/command_invalid"):
                print("{} to {}: {}".format(sender, recipient, content))

        else:  # An Actual message from a user
            print('{} to {}: {}'.format(sender, recipient, content))

        print('{}: '.format(self.name), end='', flush=True)


class Client:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.save_dir = ""

    def start(self):
        """
        Establishes the client-server_media connection. Generates a random username,
        creates and starts the Send and Receive threads, and notifies other connected clients.
        Returns:
        A Receive object representing the receiving thread.
        """

        print('Trying to connect to {}:{}...'.format(self.host, self.port))
        self.sock.connect((self.host, self.port))
        print('Successfully connected to {}:{}'.format(self.host, self.port))

        print('Welcome! Getting ready to send and receive messages...')

        # Create a directory to store client's received files
        pwd = os.getcwd()
        self.save_dir = os.path.join(pwd, 'clients_media/' + str(self.sock.getsockname()))
        if not os.path.exists(self.save_dir):
            os.makedirs(self.save_dir)

        # Create send and receive threads
        send = Send(self.sock)
        receive = Receive(send, self.sock, self.save_dir)

        # Start send and receive threads
        send.start()
        receive.start()

        print("\rAll set! Leave the chatroom anytime by typing '/quit'\n")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Chatroom Server')
    parser.add_argument('host', help='Interface the server listens at')
    parser.add_argument('-p', metavar='PORT', type=int, default=1060, help='TCP port (default 1060)')
    args = parser.parse_args()

    client = Client(args.host, args.p)
    client.start()
