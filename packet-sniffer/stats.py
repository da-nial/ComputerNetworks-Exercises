from ethernet import Ethernet
from ipv4 import IPv4
from icmp import ICMP
from tcp import TCP
from _http import _HTTP
from _https import _HTTPS
from ftp import FTP
from udp import UDP
from dns import DNS
from datetime import datetime
import os
import matplotlib.pyplot as plt
import seaborn as sns
import gc

sns.set()

TAB_1 = '\t - '
TAB_2 = '\t\t - '
TAB_3 = '\t\t\t - '
TAB_4 = '\t\t\t\t - '


class Stats:
    def __init__(self):
        self.total_count = 0

        self.ip_count = {'Src': {}, 'Dest': {}}
        self.total_fragment_count = 0
        self.fragment_count = {'TCP': 0, 'UDP': 0, 'ICMP': 0}

        self.count = {
            'Network': {'IPv4': 0},
            'Transport': {'ICMP': 0, 'TCP': 0, 'UDP': 0},
            'App': {'HTTP': 0, 'HTTPS': 0, 'FTP': 0, 'DNS': 0}
        }

        self.size = {
            'Network': {'IPv4': (0, 0, 0)},
            'Transport': {'ICMP': (0, 0, 0), 'TCP': (0, 0, 0), 'UDP': (0, 0, 0)},
            'App': {'HTTP': (0, 0, 0), 'HTTPS': (0, 0, 0), 'FTP': (0, 0, 0), 'DNS': (0, 0, 0)}
        }

        self.port_count = {'Src': {}, 'Dest': {}}
        self.report_dir = ''

    def new_packet(self, packet):
        self.total_count += 1
        link_pckt, network_pckt, transport_pckt, app_pckt = packet

        link_proto = link_pckt.__repr__()

        # link layer process:

        # network layer process:
        if not (network_pckt is None):
            network_proto = network_pckt.__repr__()

            self.update_ips(network_pckt)

            if network_pckt.is_fragmented:
                self.total_fragment_count += 1

            self.update_count('Network', network_proto)
            self.update_size('Network', network_proto, network_pckt)

            # transport layer process:
            if not (transport_pckt is None):
                self.update_ports(transport_pckt)

                transport_proto = transport_pckt.__repr__()

                self.update_count('Transport', transport_proto)
                # we pass network packet, cause that's where the packet size is stored.
                self.update_size('Transport', transport_proto, network_pckt)

                # application layer process
                if not (app_pckt is None):
                    app_proto = app_pckt.__repr__()

                    self.update_count('App', app_proto)
                    # we pass network packet, cause that's where the packet size is stored.
                    self.update_size('App', app_proto, network_pckt)

    def generate_report(self):
        now = datetime.now()
        current_time = now.strftime("%H:%M:%S")
        self.report_dir = 'Report ' + current_time
        os.mkdir(self.report_dir)
        f = open(self.report_dir + '/stats.txt', "a")

        print('#Packets: {}'.format(self.total_count), file=f)

        ipv4_report = self.count_size_report('Network', 'IPv4')
        print(ipv4_report, file=f)
        print(TAB_1 + '#Fragmented: {}'.format(self.fragment_count), file=f)

        # print(TAB_1 + 'Most Used Port: {}'.format(self.port_count))
        icmp_report = self.count_size_report('Transport', 'ICMP')
        print(icmp_report, file=f)

        tcp_report = self.count_size_report('Transport', 'TCP')
        print(tcp_report, file=f)

        http_report = self.count_size_report('App', 'HTTP')
        print(http_report, file=f)

        https_report = self.count_size_report('App', 'HTTPS')
        print(https_report, file=f)

        ftp_report = self.count_size_report('App', 'FTP')
        print(ftp_report, file=f)

        udp_report = self.count_size_report('Transport', 'UDP')
        print(udp_report, file=f)

        dns_report = self.count_size_report('App', 'DNS')
        print(dns_report, file=f)

        ip_count_report = self.ip_count_report()
        print(ip_count_report, file=f)

        port_count_report = self.port_count_report()
        print(port_count_report, file=f)

        # Pie chart of Transport Layer Protocols
        self.transport_protos_pie_chart()

        # Pie chart of App Layer Protocols
        self.app_protos_pie_chart()

        # Histogram for IP Addresses
        self.ip_frequency_hist()

        # Histogram for Ports
        self.port_frequency_hist()

        # Pie chart for Number of Fragmented IPv4 Packets
        self.fragment_pie_chart()

        # Hist chart for Transport layer sizes
        self.protos_size_hist('Transport')

        # Hist chart for App layer sizes
        self.protos_size_hist('App')

        print("Report genreated at /{}".format(self.report_dir))

    def update_ips(self, network_pckt):
        self.ip_count['Src'][network_pckt.src] = self.ip_count['Src'].get(
            network_pckt.src, 0) + 1

        self.ip_count['Dest'][network_pckt.dest] = self.ip_count['Dest'].get(
            network_pckt.dest, 0) + 1

    def update_ports(self, transport_pckt):
        transport_proto = transport_pckt.__repr__()
        if transport_proto != 'ICMP':
            self.port_count['Src'][transport_pckt.src_port] = self.port_count['Src'].get(
                transport_pckt.src_port, 0) + 1
            self.port_count['Dest'][transport_pckt.dest_port] = self.port_count['Dest'].get(
                transport_pckt.dest_port, 0) + 1

    def update_count(self, layer, proto, num=1):
        self.count[layer][proto] = self.count[layer].get(proto, 0) + 1

    def update_size(self, layer, proto, network_packet):
        new_packet_size = network_packet.total_length - \
                          (network_packet.ihl * 4)
        min_size, max_size, avg_size = self.size[layer][proto]
        min_size = min(min_size, new_packet_size)
        if min_size == 0:
            min_size = new_packet_size
        max_size = max(max_size, new_packet_size)
        avg_size = (avg_size * (self.count[layer][proto] - 1) +
                    new_packet_size) / self.count[layer][proto]

        self.size[layer][proto] = (min_size, max_size, avg_size)

    def count_size_report(self, layer, proto):
        report = TAB_1 + '{}: '.format(proto) + '\n'
        count = self.count[layer][proto]
        min_size, max_size, avg_size = self.size[layer][proto]

        report += TAB_2 + '#Packets: {:.2f}, Smallest: {:.2f}, Largest: {:.2f}, Average Size: {:.2f}'.format(
            count, min_size, max_size, avg_size) + '\n'
        return report

    def sort_ips_by_frequency(self):
        self.ip_count['Src'] = dict(
            sorted(self.ip_count['Src'].items(), key=lambda item: item[1]))

        self.ip_count['Dest'] = dict(
            sorted(self.ip_count['Dest'].items(), key=lambda item: item[1]))

    def sort_ports_by_frequency(self):
        self.port_count['Src'] = dict(
            sorted(self.port_count['Src'].items(), key=lambda item: item[1]))

        self.port_count['Dest'] = dict(
            sorted(self.port_count['Dest'].items(), key=lambda item: item[1]))

    def ip_count_report(self):
        """
            Returns Top 10 Frequent source and destination ips, as a string.
        """
        result = 'Top 10 Most Frequent Source IPs' + '\n'
        self.sort_ips_by_frequency()

        ip_count_ls = []
        for ip, count in self.ip_count['Src'].items():
            ip_count_ls.append((ip, count))
        ip_count_ls.reverse()
        for ip, count in ip_count_ls[:10]:
            result += TAB_1 + 'IP: {}, Frequency: {}'.format(ip, count) + '\n'

        result += '\n'

        result += 'Top 10 Most Frequent Destination IPs' + '\n'
        ip_count_ls = []
        for ip, count in self.ip_count['Dest'].items():
            ip_count_ls.append((ip, count))
        ip_count_ls.reverse()
        for ip, count in ip_count_ls[:10]:
            result += TAB_1 + 'IP: {}, Frequency: {}'.format(ip, count) + '\n'

        return result

    def port_count_report(self):
        """
            Returns Top 10 Frequent source and destination ports, as a string.
        """
        result = 'Top 10 Most Frequent Source Ports' + '\n'
        self.sort_ports_by_frequency()

        port_count_ls = []
        for port, count in self.port_count['Src'].items():
            port_count_ls.append((port, count))
        port_count_ls.reverse()
        for port, count in port_count_ls[:10]:
            result += TAB_1 + \
                      'Port: {}, Frequency: {}'.format(port, count) + '\n'

        result += '\n'

        result += 'Top 10 Most Frequent Destination Ports' + '\n'
        port_count_ls = []
        for port, count in self.port_count['Dest'].items():
            port_count_ls.append((port, count))
        port_count_ls.reverse()
        for port, count in port_count_ls[:10]:
            result += TAB_1 + \
                      'Port: {}, Frequency: {}'.format(port, count) + '\n'

        return result

    def transport_protos_pie_chart(self, num=0):
        plt.figure(num=None, figsize=(16, 12), dpi=300)
        transport_protos = list(self.count['Transport'].keys())
        transport_protos_count = list(self.count['Transport'].values())
        plt.pie(transport_protos_count, labels=transport_protos,
                explode=(0, 0.1, 0), autopct='%1.0f%%')
        plt.axis('equal')
        plt.savefig(self.report_dir + '/Transport Layer Protocols.png')

        plt.cla()
        plt.clf()
        plt.close('all')
        gc.collect()

    def app_protos_pie_chart(self, num=1):
        plt.figure(num=None, figsize=(16, 12), dpi=300)
        app_protos = list(self.count['App'].keys())
        app_protos_count = list(self.count['App'].values())
        plt.pie(app_protos_count, labels=app_protos, autopct='%1.0f%%')
        plt.axis('equal')
        plt.savefig(self.report_dir + '/Application Layer Protocols.png')

        plt.cla()
        plt.clf()
        plt.close('all')
        gc.collect()

    def ip_frequency_hist(self, num=2):
        self.sort_ips_by_frequency()

        plt.figure(num=None, figsize=(24, 16), dpi=300)
        plt.xticks(rotation=45)

        ip_count_ls = []
        for ip, count in self.ip_count['Src'].items():
            ip_count_ls.append((ip, count))
        ip_count_ls.reverse()

        src_ips = []
        src_ip_counts = []
        for ip, count in ip_count_ls[:10]:
            src_ips.append(ip)
            src_ip_counts.append(count)
        plt.bar(src_ips, src_ip_counts)
        plt.savefig(self.report_dir + '/Source IP Frequency.png')

        plt.cla()
        plt.clf()
        plt.close('all')
        gc.collect()

        plt.figure(num=None, figsize=(24, 16), dpi=300)
        plt.xticks(rotation=45)

        ip_count_ls = []
        for ip, count in self.ip_count['Dest'].items():
            ip_count_ls.append((ip, count))
        ip_count_ls.reverse()

        dest_ips = []
        dest_ip_counts = []
        for ip, count in ip_count_ls[:10]:
            dest_ips.append(ip)
            dest_ip_counts.append(count)
        plt.bar(dest_ips, dest_ip_counts)
        plt.savefig(self.report_dir + '/Destination IP Frequency.png')

        plt.cla()
        plt.clf()
        plt.close('all')
        gc.collect()

    def port_frequency_hist(self, num=4):
        self.sort_ports_by_frequency()

        plt.figure(num=None, figsize=(24, 16), dpi=300)
        plt.xticks(rotation=45)

        port_count_ls = []
        for port, count in self.port_count['Src'].items():
            port_count_ls.append((port, count))
        port_count_ls.reverse()

        src_ports = []
        src_port_counts = []
        for port, count in port_count_ls[:10]:
            src_ports.append(port)
            src_port_counts.append(count)
        src_ports = list(map(str, src_ports))
        plt.bar(src_ports, src_port_counts)
        plt.savefig(self.report_dir + '/Source Port Frequency.png')

        plt.cla()
        plt.clf()
        plt.close('all')
        gc.collect()

        plt.figure(num=None, figsize=(24, 16), dpi=300)
        plt.xticks(rotation=45)

        port_count_ls = []
        for port, count in self.port_count['Dest'].items():
            port_count_ls.append((port, count))
        port_count_ls.reverse()

        dest_ports = []
        dest_port_counts = []
        for port, count in port_count_ls[:10]:
            dest_ports.append(port)
            dest_port_counts.append(count)
        dest_ports = list(map(str, dest_ports))
        plt.bar(dest_ports, dest_port_counts)
        plt.savefig(self.report_dir + '/Destination Port Frequency.png')

        plt.cla()
        plt.clf()
        plt.close('all')
        gc.collect()

    def fragment_pie_chart(self, num=6):
        plt.figure(num=None, figsize=(16, 12), dpi=300)

        plt.pie([self.total_fragment_count, self.total_count - self.total_fragment_count],
                labels=['Fragmented', 'Not Fragmented'],
                explode=(0, 0.1), autopct='%1.0f%%')
        plt.axis('equal')
        plt.savefig(self.report_dir + '/IPv4 Fragment Ratio.png')

        plt.cla()
        plt.clf()
        plt.close('all')
        gc.collect()

    def protos_size_hist(self, layer):
        plt.figure(num=None, figsize=(24, 16), dpi=300)
        plt.xticks(rotation=90)

        protos = self.size[layer].keys()
        protos_unpacked = []
        for proto in protos:
            min_bin = proto + ' min'
            max_bin = proto + ' max'
            avg_bin = proto + ' avg'
            protos_unpacked += [min_bin, max_bin, avg_bin]

        protos_size_unpacked = []
        for proto in protos:
            min_size, max_size, avg_size = self.size[layer][proto]
            protos_size_unpacked += [min_size, max_size, avg_size]

        barlist = plt.bar(protos_unpacked, protos_size_unpacked)
        for i in range(len(barlist)):
            if i % 3 == 0:
                barlist[i].set_color('r')
            elif i % 3 == 1:
                barlist[i].set_color('g')
            else:
                barlist[i].set_color('b')

        plt.savefig(self.report_dir + '/{} Protos Size.png'.format(layer))

        plt.cla()
        plt.clf()
        plt.close('all')
        gc.collect()
