import struct


class TCP:
    def __init__(self, data):
        self.src_port, self.dest_port, self.seq_num, self.ack, offset_reserved_flags = struct.unpack(
            '! H H L L H', data[:14])
        offset = (offset_reserved_flags >> 12) * 4
        self.flag_urg = (offset_reserved_flags & 32) >> 5
        self.flag_ack = (offset_reserved_flags & 16) >> 4
        self.flag_psh = (offset_reserved_flags & 8) >> 3
        self.flag_rst = (offset_reserved_flags & 4) >> 2
        self.flag_syn = (offset_reserved_flags & 2) >> 1
        self.flag_fin = offset_reserved_flags & 1

        self.payload = data[offset:]

    def __repr__(self):
        return 'TCP'
