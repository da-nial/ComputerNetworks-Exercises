import struct


class ICMP:
    def __init__(self, data):
        self.type, self.code, checksum = struct.unpack(
            '! B B H', data[:4])
        # Checksum is converted to its binary repr as a string.
        self.checksum = '{:16b}'.format(checksum)
        self.payload = data[4:]

    def __repr__(self):
        return 'ICMP'


def get_icmp_description(type, code):
    """
        Returns Description of ICMP Packet according to it type and code.
        Reference: https://tools.ietf.org/html/rfc792
    """
    icmp_types = {
        0: 'Echo Reply',
        3: 'Destination Unreachable',
        4: 'Source Quench',
        5: 'Redirect',
        8: 'Echo',
        11: 'Time Exceeded',
        12: 'Parameter Problem',
        13: 'Timestamp',
        14: 'Timestamp Reply',
        15: 'Information Request',
        16: 'Information Reply'
    }

    unreachable_codes = {
        0: 'net unreachable',
        1: 'host unreachable',
        2: 'protocol unreachable',
        3: 'port unreachable',
        4: 'fragmentation needed and DF set',
        5: 'source route failed'
    }

    redirect_codes = {
        0: 'Redirect datagrams for the Network',
        1: ' Redirect datagrams for the Host',
        2: 'Redirect datagrams for the Type of Service and Network',
        3: 'Redirect datagrams for the Type of Service and Host'
    }

    time_exceeded_codes = {
        0: 'time to live exceeded in transit',
        1: 'fragment reassembly time exceeded'
    }

    icmp_description = icmp_types[type]
    if type == 3 and code in unreachable_codes:
        icmp_description += '|' + unreachable_codes[code]
    elif type == 5 and code in redirect_codes:
        icmp_description += '|' + redirect_codes[code]
    elif type == 11 and code in time_exceeded_codes:
        icmp_description += '|' + time_exceeded_codes[code]

    return icmp_description
