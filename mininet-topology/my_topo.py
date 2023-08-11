from mininet.topo import Topo


class MyTopo(Topo):

    def __init__(self):

        Topo.__init__(self)

        # Add hosts
        h1 = self.addHost(
            'h1', ip='10.0.1.100/24', defaultRoute='via 10.0.1.1')
        h2 = self.addHost(
            'h2', ip='10.0.2.100/24', defaultRoute='via 10.0.2.1')
        h3 = self.addHost(
            'h3', ip='10.0.3.100/24', defaultRoute='via 10.0.3.1')

        s1 = self.addSwitch('s1')

        # Add links
        self.addLink(h1, s1)
        self.addLink(h2, s1)
        self.addLink(h3, s1)


topos = {'mytopo': (lambda: MyTopo())}
