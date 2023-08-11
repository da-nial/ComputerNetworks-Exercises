# import struct
# from struct import calcsize


# # arr = bytes(5)
# # print(arr)
# # print(type(arr))
# # print(len(arr))


# # print(chr(49))


# # raw_data_14 = b'\x00PV\xe1i\xf9\x00\x0c)`\x8a\x1e\x08\x00'


import sys
import select
import os

# i = 0
# while True:
#     os.system('cls' if os.name == 'nt' else 'clear')
#     print("I'm doing stuff. Press Enter to stop me!")
#     print(i)
#     if sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
#         line = input()
#         break
#     i += 1


a = bin(10)
print('a: {}'.format(a))
print(type(a))
print('a[0]: {}'.format(a[0]))
