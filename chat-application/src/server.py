import argparse
import os
import socket
import threading
from datetime import datetime

from .utils import db_connection, pack_message, unpack_message, generate_name, send_file, recv_file


class Server(threading.Thread):
    def __init__(self, host, port, db):
        super().__init__()
        self.connections = []
        self.host = host
        self.port = port
        self.can_broadcast = True

        # Create a directory to store client's received files
        pwd = os.getcwd()
        self.save_dir = os.path.join(pwd, 'server_media/')
        if not os.path.exists(self.save_dir):
            os.makedirs(self.save_dir)

        try:
            self.conn = db_connection(db)
            print('Connected to database successfully')

        except:
            print("Oh no! An error occured! Connection to database failed")

    def run(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((self.host, self.port))

        sock.listen(1)
        print('Listening at ', sock.getsockname())

        while True:
            # Accept a new connection
            sc, sockname = sock.accept()
            print('Accepted a new connection from {} to {}'.format(sc.getpeername(), sc.getsockname()))

            username = generate_name()
            print('Assigned Name to connection {} is {}'.format(sc.getpeername(), username))
            self.add_user(sc.getpeername(), username)

            # Create a new thread
            server_socket = ServerSocket(sc, sockname, self)

            message = pack_message('Server', username, "INIT_USERNAME={}".format(username))
            server_socket.send(message)

            # Start the new thread
            server_socket.start()

            # Add the thread to active connections
            self.connections.append(server_socket)

            print('Ready to receive messages from ', sc.getpeername())

    def add_user(self, address, username):
        """
        Add a new user to the routing_table of server.
        As the initial username of each user is unique, this function doesn't check for a duplicate username.
        :param address:
        :param username:
        :return: If successful, row id of the newly added user. A negative value otherwise.
        """
        cur = self.conn.cursor()
        cur.execute(''' INSERT INTO routing_table(address,username,status)
                              VALUES(?,?,?) ''', (str(address), username, 1))
        self.conn.commit()
        return cur.lastrowid

    def broadcast(self, message, source=None):
        """
        Sends a message to all connected clients, except the source of the message.
        Args:
            message (str): The message to broadcast.
            source (tuple): The socket address of the source client.
        """
        for connection in self.connections:
            # Send to all connected clients except the source client
            if connection.sockname != source:
                connection.send(message)

    def broadcast_file(self, message, source):
        pass

    def send_message_to(self, message, destination):
        if self.username_exists(destination):
            # Find the connection from list and db
            user_address = self.get_user_address(destination)
            for connection in self.connections:
                if str(connection.sc.getpeername()) == user_address:
                    connection.send(message)
                    break

        elif self.group_name_exists(destination):
            members_address = self.get_members_address(destination)
            for connection in self.connections:
                if str(connection.sc.getpeername()) in members_address:
                    connection.send(message)

    def send_file_to(self, message, filename, filesize, destination):
        if self.username_exists(destination):
            # Find the connection from list and db
            address = self.get_user_address(destination)
            for connection in self.connections:
                if str(connection.sc.getpeername()) == address:
                    connection.send_file(message, filename, filesize)
                    break

        elif self.group_name_exists(destination):
            members_address = self.get_members_address(destination)
            for connection in self.connections:
                if str(connection.sc.getpeername()) in members_address:
                    connection.send_file(message, filename, filesize)

    def username_exists(self, username):
        """
            Checks whether the given username exists in database.
            :returns True if exists, False if it does not exist.
        """
        cur = self.conn.cursor()
        cur.execute("""SELECT username
                       FROM routing_table
                       WHERE username=? """,
                    (username,))
        existing_username = cur.fetchone()
        return not (existing_username is None)

    def get_user_address(self, username):
        cur = self.conn.cursor()
        cur.execute("""SELECT address
                       FROM routing_table
                       WHERE username=?""",
                    (username,))
        found_users = cur.fetchone()
        return found_users[0]

    def get_user_username(self, address):
        cur = self.conn.cursor()
        cur.execute("""SELECT username
                       FROM routing_table
                       WHERE address=?""",
                    (address,))
        found_users = cur.fetchone()
        return found_users[0]

    def update_username(self, user_address, new_username):
        """
        Updates the username of the given address to the given new username, if the new one is available.
        :param user_address: ip and port address of the user
        :param new_username: the requested new username
        :return: if successful, row id of the newly added user. A negative value otherwise.
        """
        cur = self.conn.cursor()

        if self.name_exists(new_username):
            # Username already taken
            return -1
        else:
            old_username = self.get_user_username(str(user_address))

            cur.execute(''' UPDATE routing_table
                            SET username = ?
                            WHERE address = ?''', (new_username, str(user_address)))
            self.conn.commit()

            # Notify all users that this user has changed their username
            message = pack_message("Server", 'broadcast',
                                   "User {} has changed their username to {}!"
                                   " If you want to chat with them,"
                                   " you need to enter command `/change-chat {}`"
                                   .format(old_username, new_username, new_username))
            self.broadcast(message)
            return cur.lastrowid

    def online_users(self):
        """
        :return: a list of all usernames that are currently online
        """
        cur = self.conn.cursor()
        cur.execute("""SELECT username
                       FROM routing_table
                       WHERE status=?
                    """, (1,))
        users = cur.fetchall()

        return users

    def remove_connection(self, connection):
        """
        Removes a ServerSocket thread from the connections attribute.
        Args:
            connection (ServerSocket): The ServerSocket thread to remove.
        """
        # TODO make it offline in db
        self.connections.remove(connection)

    def make_offline(self, connection):
        user_address = connection.sc.getpeername()

        cur = self.conn.cursor()
        cur.execute(''' UPDATE routing_table
                        SET status = ?
                        WHERE address = ?''', (0, str(user_address)))
        self.conn.commit()

    def create_group(self, user_address, group_name):
        """
            Creates a new group, adds it to groups table in database,
            adds its creator to user_groups table
            As the desired group name could be duplicate, this function first checks whether the group name is already used or not.
            :param address:
            :param username:
            :return: If successful, row id of the newly added user. A negative value otherwise.
        """
        if self.name_exists(group_name):
            return -1
        else:
            cur = self.conn.cursor()
            cur.execute(''' INSERT INTO groups(name, creator_address, creation_date)
                            VALUES(?,?,?) ''', (group_name, user_address, str(datetime.now())))
            created_group_id = cur.lastrowid

            cur.execute(''' INSERT INTO users_groups(user_address, group_id)
                            VALUES(?,?) ''', (user_address, created_group_id))

            self.conn.commit()
            return cur.lastrowid

    def get_group_id(self, group_name):
        """
            Checks whether the given group_name exists in database.
            :returns True if exists, False if it does not exist.
        """
        cur = self.conn.cursor()
        cur.execute("""SELECT id
                       FROM groups
                       WHERE name=? """,
                    (group_name,))
        found_group = cur.fetchone()
        return found_group[0]

    def group_name_exists(self, group_name):
        """
            Checks whether the given group_name exists in database.
            :returns True if exists, False if it does not exist.
        """
        cur = self.conn.cursor()
        cur.execute("""SELECT name
                       FROM groups
                       WHERE name=? """,
                    (group_name,))
        found_group = cur.fetchone()
        return not (found_group is None)

    def is_member_of(self, user_address, group_name):
        cur = self.conn.cursor()

        group_id = self.get_group_id(group_name)

        cur.execute("""SELECT id
                       FROM users_groups
                       WHERE user_address=? AND 
                       group_id=?""",
                    (user_address, group_id))

        found_group = cur.fetchone()
        return not (found_group is None)

    def join_group(self, user_address, group_name):
        cur = self.conn.cursor()
        if not self.group_name_exists(group_name):
            return -1
        elif self.is_member_of(user_address, group_name):
            return 0
        else:
            group_id = self.get_group_id(group_name)
            cur.execute(''' INSERT INTO users_groups(user_address, group_id)
                            VALUES(?,?) ''',
                        (user_address, group_id))
            self.conn.commit()
            username = self.get_user_username(user_address)
            message = pack_message("Sender", group_name, "{} just joined the group {}!".format(username, group_name))
            self.send_message_to(message, group_name)
            return cur.lastrowid

    def show_groups(self):
        cur = self.conn.cursor()
        cur.execute("""SELECT *
                       FROM groups
                    """)

        groups = cur.fetchall()
        return groups

    def leave_group(self, user_address, group_name):
        cur = self.conn.cursor()
        if not self.group_name_exists(group_name):
            return -1
        elif not self.is_member_of(user_address, group_name):
            return 0
        else:
            group_id = self.get_group_id(group_name)
            cur.execute(''' DELETE FROM users_groups
                            WHERE user_address = ? AND 
                            group_id = ?''',
                        (user_address, group_id))
            self.conn.commit()

            username = self.get_user_username(user_address)
            message = pack_message("Sender", group_name, "{} left the group {}!".format(username, group_name))
            self.send_message_to(message, group_name)
            return cur.lastrowid

    def get_members_address(self, group_name):
        group_id = self.get_group_id(group_name)
        cur = self.conn.cursor()
        cur.execute("""SELECT user_address
                       FROM users_groups
                       WHERE group_id=?""",
                    (group_id,))
        found_members = cur.fetchall()
        found_members_clean = []
        for member in found_members:
            found_members_clean.append(member[0])
        return found_members_clean

    def name_exists(self, name):
        return self.username_exists(name) or self.group_name_exists(name)


class ServerSocket(threading.Thread):
    def __init__(self, sc, sockname, server):
        super().__init__()
        self.sc = sc
        self.sockname = sockname
        self.server = server

    def run(self):
        while True:
            message = self.sc.recv(1024)
            if message:
                print('{}: {!r}'.format(self.sockname, message))
                try:
                    self.parse(message)
                except ValueError:
                    print(ValueError.with_traceback())

            else:
                # Client has closed the socket, exit the thread
                # TODO add name! and broadcast to all that they left! and change their status to offline!
                left_username = self.server.get_user_username(str(self.sc.getpeername()))
                content = '{} left the chatroom!'.format(left_username)
                message = pack_message('Server', 'broadcast', content)
                self.server.broadcast(message, self.sockname)
                print(message)
                self.sc.close()
                self.server.remove_connection(self)
                self.server.make_offline(self)
                return

    def send(self, message):
        self.sc.sendall(message)

    def send_file(self, message, filename, filesize):
        print('LINE 201, MESSAGE: ' + str(message))
        self.sc.sendall(message)
        send_file(self.sc, 'server_media/' + str(filename), filesize)

    def parse(self, message):
        sender, recipient, content = unpack_message(message)

        if content.startswith("/"):  # Its a command
            if content.startswith("/send-file"):
                _, filename, filesize = content.split()
                filesize = int(filesize)
                # TODO each client should have its own directory in server_media!
                # TODO broadcast file?
                recv_file(self.sc, filename, filesize, 'server_media')
                self.server.send_file_to(message, filename, filesize, recipient)

            elif content.startswith("/change-chat"):
                _, new_recipient = content.split()
                if self.server.name_exists(new_recipient) or \
                        (new_recipient == 'broadcast' and self.server.can_broadcast):
                    content = "/change-chat_result:new_recipient=" + new_recipient
                else:
                    content = "/change-chat_result:new_recipient=-1"

                message = pack_message('Server', sender, content)
                print(message)
                self.send(message)

            elif content.startswith("/change-username"):
                _, new_username = content.split()
                result = self.server.update_username(self.sc.getpeername(), new_username)
                if result == -1:
                    content = "/change-username_result:new_username=-1"
                else:
                    content = "/change-username_result:new_username=" + new_username
                message = pack_message('Server', sender, content)
                print(message)
                self.send(message)

            elif content.startswith("/online-users"):
                online_users = self.server.online_users()
                content = "/online-users\n"
                for user in online_users:
                    content += user[0] + '\n'
                message = pack_message('Server', sender, content)
                print(message)
                self.send(message)

            elif content.startswith("/create-group"):
                _, group_name = content.split()
                result = self.server.create_group(str(self.sc.getpeername()), group_name)
                if result == -1:  # Group Exists
                    content = "/create-group_result:create_group=-1"
                elif result >= 0:  # Group Created Successfully
                    content = "/create-group_result:create_group=" + group_name
                message = pack_message('Server', sender, content)
                print(message)
                self.send(message)

            elif content.startswith("/join-group"):
                _, group_name = content.split()
                result = self.server.join_group(str(self.sc.getpeername()), group_name)
                if result == -1:
                    content = "/join-group_result:join_group=-1"
                elif result == 0:
                    # Already Joined!
                    content = "/join-group_result:join_group=0"
                elif result > 0:
                    # Joined Succesfully!
                    content = "/join-group_result:join_group=" + group_name

                message = pack_message('Server', sender, content)
                print(message)
                self.send(message)

            elif content.startswith("/show-groups"):
                groups = self.server.show_groups()
                print(groups)
                # TODO add number of group members
                content = "/show-groups_result=\n"
                for group in groups:
                    content += str(group) + '\n'

                message = pack_message('Server', sender, content)
                print(message)
                self.send(message)

            elif content.startswith("/leave-group"):
                _, group_name = content.split()
                result = self.server.leave_group(str(self.sc.getpeername()), group_name)
                if result == -1:
                    # There is no such group
                    content = "/leave-group_result:leave_group=-1"
                elif result == 0:
                    # Group Exists, But this client is not a member of it. (i.e. already left!)
                    content = "/leave-group_result:leave_group=0"
                elif result > 0:
                    # Left Successfully!
                    content = "/leave-group_result:leave_group=" + group_name

                message = pack_message('Server', sender, content)
                print(message)
                self.send(message)

            else:
                content = "/command_invalid"
                message = pack_message('Server', sender, content)
                print(message)
                self.send(message)

        else:  # Its a message
            # Actually send a message to recipient!
            if recipient == 'broadcast':
                self.server.broadcast(message, self.sockname)
            else:
                self.server.send_message_to(message, recipient)


def exit(server):
    while True:
        ipt = input('')
        if ipt == 'q':
            print('Closing all connections')
            for connection in server.connections:
                connection.sc.close()
            print('shutting down the server_media')
            os._exit(0)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Chatroom Server')
    parser.add_argument('host', help='Interface the server listens at')
    parser.add_argument('-p', metavar='PORT', type=int, default=1060,
                        help='TCP port (default 1060)')
    parser.add_argument('-db', metavar='DATABSE', type=str, default='db.sqlite',
                        help='Database Path (The Defualt is set to file "db.sqlite"'
                             ' which should be located in the same directory that server.py is in)')
    args = parser.parse_args()

    # Create and start server thread
    server = Server(args.host, args.p, args.db)
    server.start()

    exit = threading.Thread(target=exit, args=(server,))
    exit.start()
