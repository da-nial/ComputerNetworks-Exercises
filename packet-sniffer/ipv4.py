import struct


class IPv4:
    def __init__(self, data):
        version_ihl, tos, total_length, identification, flags_fragment_offset, ttl, proto, checksum, src, dest = struct.unpack(
            '! B B h h h B B h 4s 4s', data[0:20])

        flags_fragment_offset = '{:016b}'.format(flags_fragment_offset)

        self.version = version_ihl >> 4
        self.ihl = (version_ihl & 15)  # in words

        self.tos = tos
        self.total_length = total_length  # (header + payload) size in bytes

        self.identification = identification
        self.flags = flags_fragment_offset[:3]
        self.fragmentation_offset = flags_fragment_offset[3:]

        if self.flags[1] == '1' or self.fragmentation_offset == '0000000000000':
            self.is_fragmented = False
        else:
            self.is_fragmented = True

        self.ttl = ttl
        self.proto = proto  # upper layer protocol
        self.checksum = checksum  # is h the right format?

        self.src = get_ipv4_addr(src)
        self.dest = get_ipv4_addr(dest)

        self.payload = data[self.ihl * 4:]

    def __repr__(self):
        return 'IPv4'


def get_ipv4_addr(addr_raw):
    """
        Converts ip address from bytes string to (192.168.1.1) format
    """
    return '.'.join(map(str, addr_raw))


def get_tos_description(tos):
    """
        Returns Description of given Type of Service Decimal
        in IPv4 Header according to https://tools.ietf.org/html/rfc791
        The first 3 bits specify the packets precedence, the next 3 bits specify desired quality of service.
    """
    tos_precedence = {'000': 'Routine',
                      '001': 'Priority',
                      '010': 'Immediate',
                      '011': 'Flash',
                      '100': 'Flash Override',
                      '101': 'Critical',
                      '110': 'Internetwork Control',
                      '111': 'Network Control'}

    _tos = '{:08b}'.format(tos)

    description = 'Precedence: ' + tos_precedence[_tos[:3]]

    if _tos[3] == '1':
        description += '|Low Delay'

    if _tos[4] == '1':
        description += '|High Throughput'

    if _tos[5] == '1':
        description += '|High Reliability'

    return description


def get_flags_description(flags):
    description = ''
    if flags[1] == '1':
        description = "Don't Fragment"
    else:
        description = 'May Fragment'
        if flags[2] == '1':
            description += '|More Fragments'
        else:
            description += '|Last Fragment'

    return description
