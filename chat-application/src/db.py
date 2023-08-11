import sqlite3

conn = sqlite3.connect('db.sqlite')

cursor = conn.cursor()

print('Opened Database successfully')

# ================ Creating Users Routing Table =============

cursor.execute('''CREATE TABLE routing_table
         (
         address TEXT PRIMARY KEY,
         username          TEXT,
         status INTEGER DEFAULT 1
         );
         ''')

# ================ End of Creating Users Routing table =============


# ================ TESTING =============

# user = ('localhost:8080', 'nialda', 1)
#
# cursor.execute(''' INSERT INTO routing_table(address,username,status)
#                   VALUES(?,?,?) ''', user)
#
# username = ('nialda', )
#
# cursor.execute("""SELECT username
#                   FROM routing_table
#                   WHERE username=?
#                """,
#                username)
#
# existing_username = cursor.fetchone()
#
# print(not (existing_username is None))
#
# cursor.execute(''' UPDATE routing_table
#                    SET username = ?
#                    WHERE address = ?''', ('TheDanialH', 'localhost:8080'))
# conn.commit()


# cursor.execute('''CREATE TABLE GROUPS
#          (
#          id INTEGER PRIMARY KEY,
#          ADDRESS CHAR(50) PRIMARY KEY     NOT NULL,
#          GROUP           CHAR(10)
#          );
#          ''')

# ================ END OF TESTING =============


# ================ Creating Groups  Table =============

# TODO SET ID TO AUTOINCREMENT!

cursor.execute('''CREATE TABLE groups
         (
         id INTEGER PRIMARY KEY,
         name TEXT,
         creator_address TEXT,
         creation_date          TEXT
         );
         ''')

# ================ End of Creating Users Routing table =============


cursor.execute('''CREATE TABLE users_groups
         (
         id INTEGER PRIMARY KEY,
         user_address TEXT,
         group_id          TEXT
         );
         ''')

conn.commit()

cursor.close()
#
#
# cursor.execute("""SELECT name
#                        FROM groups
#                        WHERE name=? """,
#                     ('EFLIJ',))
#
# found_group = cursor.fetchone()
# print("found_grouppp: " + str(found_group))
