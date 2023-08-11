import struct


class UDP:

    def __init__(self, data):
        self.src_port, self.dest_port, self.length, checksum = struct.unpack(
            '! H H H H', data[:8])
        self.checksum = '{:16b}'.format(checksum)
        self.payload = data[8:]

    def __repr__(self):
        return 'UDP'
