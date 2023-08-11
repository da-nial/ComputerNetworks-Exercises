import socket
import struct


class Ethernet:
    def __init__(self, raw_data):
        dest, src, proto = struct.unpack('! 6s 6s H', raw_data[:14])
        self.dest_mac = get_mac_addr(dest)
        self.src_mac = get_mac_addr(src)
        self.proto = socket.htons(proto)
        self.payload = raw_data[14:]

    def __repr__(self):
        return 'Ethernet'


def get_mac_addr(mac_raw):
    """
        Converts MAC Address to (ie AA:BB:CC:DD:EE:FF) format, from bytes string.
    """
    byte_str = map('{:02x}'.format, mac_raw)
    mac_addr = ':'.join(byte_str).upper()
    return mac_addr


def get_ether_proto_name(proto_num):
    """
        Returns ethernet protocol name of the given protocol number.
        protocol names reference: https://www.iana.org/assignments/ieee-802-numbers/ieee-802-numbers.xhtml
    """
    ether_protos = {2048: 'IPv4', 2050: 'NBS Internet',
                    0000: 'IEEE802.3 Length Field', 1536: 'XEROX NS IDP'}
    if proto_num in ether_protos:
        return ether_protos[proto_num]
    else:
        return '?'


def get_internet_proto_name(proto_num):
    """
        Returns Internet protocol name of the given protocol number.
        protocol names reference: https://tools.ietf.org/html/rfc790
    """
    internet_protos = {1: 'ICMP', 6: 'TCP', 7: 'UCL', 17: 'UDP'}
    if proto_num in internet_protos:
        return internet_protos[proto_num]
    else:
        return '?'
