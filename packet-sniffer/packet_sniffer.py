import socket
import threading
from stats import Stats
from ethernet import Ethernet, get_mac_addr, get_internet_proto_name, get_ether_proto_name
from ipv4 import IPv4, get_tos_description, get_flags_description
from icmp import ICMP, get_icmp_description
from tcp import TCP
from udp import UDP
from _http import _HTTP
from _https import _HTTPS
from ftp import FTP
from dns import DNS
from helper import *

TAB_1 = '\t - '
TAB_2 = '\t\t - '
TAB_3 = '\t\t\t - '
TAB_4 = '\t\t\t\t - '

DATA_TAB_1 = '\t   '
DATA_TAB_2 = '\t\t   '
DATA_TAB_3 = '\t\t\t   '
DATA_TAB_4 = '\t\t\t\t   '

cont = True
reported = False


def controller():
    global cont
    global reported
    while True:
        input()
        cont = not cont
        reported = False


def main():
    global cont
    global reported
    conn = socket.socket(socket.AF_PACKET, socket.SOCK_RAW, socket.ntohs(3))
    stats = Stats()

    pckt_num = 0
    while True:
        while cont:
            pckt_num += 1
            raw_data, addr = conn.recvfrom(65535)

            link_pckt, network_pckt, transport_pckt, app_pckt = None, None, None, None

            # Preprocess, Extract interface name, ethernet protocol, ethernet name
            if_name, proto_num = addr[0], addr[1]
            proto_name = get_ether_proto_name(proto_num)
            print('\nPacket Num: {}, IF: {}, Ethernet Protocol Number: {} ({})'.format(
                pckt_num, if_name, proto_num, proto_name))

            # Examine Link Header (Layer 1), Extract source and destination physical address and ethernet protocol.
            eth = Ethernet(raw_data)
            link_pckt = eth

            print('Ethernet Frame:')
            print(TAB_1 + 'Protocol: {}, Source: {}, Destination: {}'.format(eth.proto,
                                                                             eth.src_mac,
                                                                             eth.dest_mac))

            if eth.proto == 8:  # It is an IPv4 packet
                # Examine Network Header (Layer 2), Extract Packet Version, Header Length, Type of Service,
                #  Total Length, Fragmentation Status, Time to Live, Protocol, Source and Destination IP address.
                ipv4 = IPv4(eth.payload)
                network_pckt = ipv4

                print(TAB_1 + 'IPv4 Packet:')
                print(TAB_2 + 'Version: {}, Header Length: {} words, ToS: {} ({}),'.format(ipv4.version,
                                                                                           ipv4.ihl,
                                                                                           ipv4.tos,
                                                                                           get_tos_description(ipv4.tos)))
                print(TAB_2 + 'Total Length: {} bytes, Flags: {} ({})'.format(ipv4.total_length,
                                                                              ipv4.flags,
                                                                              get_flags_description(ipv4.flags)))
                print(TAB_2 + 'isFragmented: {}, Fragmentation Offset: {}, TTL: {}'.format(ipv4.is_fragmented,
                                                                                           ipv4.fragmentation_offset,
                                                                                           ipv4.ttl))
                print(TAB_2 + 'Protocol: {} ({}), Source: {}, Destination: {}'.format(
                    ipv4.proto, get_internet_proto_name(ipv4.proto), ipv4.src, ipv4.dest))

                if ipv4.proto == 1:  # It is an ICMP packet
                    # Examine ICMP Header, Extract ICMP Type, Code and Checksum.
                    # An abstract description of icmp types and codes are added, but complete details are ignored.
                    icmp = ICMP(ipv4.payload)
                    transport_pckt = icmp

                    print(TAB_2 + 'ICMP Packet:')
                    print(TAB_3 + 'Type: {}, Code: {} ({}), Checksum: {},'.format(icmp.type,
                                                                                  icmp.code,
                                                                                  get_icmp_description(
                                                                                      icmp.type, icmp.code),
                                                                                  icmp.checksum))
                    print(TAB_4 + 'ICMP Data:')
                    # print(format_multi_line(DATA_TAB_3, icmp.payload))

                elif ipv4.proto == 6:  # It is a TCP packet
                    tcp = TCP(ipv4.payload)
                    transport_pckt = tcp

                    print(TAB_2 + 'TCP Segment:')
                    print(TAB_3 + 'Source Port: {}, Destination Port: {}'.format(tcp.src_port,
                                                                                 tcp.dest_port))
                    print(TAB_3 + 'Sequence Number: {}, Acknowledgment: {}'.format(tcp.seq_num,
                                                                                   tcp.ack))
                    print(TAB_3 + 'Flags:')
                    print(TAB_4 + 'URG: {}, ACK: {}, PSH: {}'.format(tcp.flag_urg,
                                                                     tcp.flag_ack,
                                                                     tcp.flag_psh))
                    print(TAB_4 + 'RST: {}, SYN: {}, FIN:{}'.format(tcp.flag_rst,
                                                                    tcp.flag_syn,
                                                                    tcp.flag_fin))

                    # Check if it is an HTTP packet
                    if tcp.src_port == 80 or tcp.dest_port == 80:
                        http = _HTTP(tcp.payload)
                        app_pckt = http

                        http_info = str(http.data).split('\n')
                        try:
                            for line in http_info:
                                print(DATA_TAB_3 + str(line))
                        except:
                            print(TAB_4 + 'Unable to print HTTP Message')

                    elif tcp.src_port == 443 or tcp.dest_port == 443:
                        https = _HTTPS(tcp.payload)
                        app_pckt = https

                        # https_info = str(https.data).split('\n')
                        # try:
                        #     for line in https_info:
                        #         print(DATA_TAB_3 + str(line))
                        # except:
                        #     print(TAB_4 + 'Unable to print HTTPS Message')

                    # Check if it is an FTP packet
                    elif tcp.src_port == 21 or tcp.dest_port == 21:
                        ftp = FTP(tcp.payload)
                        app_pckt = ftp

                elif ipv4.proto == 17:  # It is a UDP packet
                    udp = UDP(ipv4.payload)
                    transport_pckt = udp

                    print(TAB_1 + 'UDP Segment:')
                    print(TAB_2 + 'Source Port: {}, Destination Port: {}, Length: {}, Checksum: {}'.format(udp.src_port,
                                                                                                           udp.dest_port,
                                                                                                           udp.length,
                                                                                                           udp.checksum))

                    # Check if it is a DNS packet
                    if udp.src_port == 53 or udp.dest_port == 53:
                        dns = DNS(udp.payload)
                        app_pckt = dns

                else:  # Not ICMP, TCP, and UDP
                    print(TAB_1 + 'Unknown Transport Layer Protocol')

            stats.new_packet(
                (link_pckt, network_pckt, transport_pckt, app_pckt))

        if not reported:
            stats.generate_report()
            reported = True


if __name__ == "__main__":
    controller = threading.Thread(target=controller, args=())
    controller.start()
    main()
