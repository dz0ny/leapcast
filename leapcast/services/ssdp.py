# -*- coding: utf8 -*-

from __future__ import unicode_literals
import socket
from twisted.internet import reactor
from twisted.internet.protocol import DatagramProtocol
from leapcast.utils import render


class SSDP(DatagramProtocol):
    SSDP_ADDR = '239.255.255.250'
    SSDP_PORT = 1900
    header = '''\
    HTTP/1.1 200 OK\r
    LOCATION: http://$ip:8008/ssdp/device-desc.xml\r
    CACHE-CONTROL: max-age=1800\r
    CONFIGID.UPNP.ORG: 7337\r
    BOOTID.UPNP.ORG: 7337\r
    USN: uuid:94147b27-fb93-5a2a-b502-66b49524242f\r
    ST: urn:dial-multiscreen-org:service:dial:1\r
    \r
    '''

    def __init__(self):
        self.transport = reactor.listenMulticast(
            self.SSDP_PORT, self, listenMultiple=True)
        self.transport.setLoopbackMode(1)
        self.transport.joinGroup(self.SSDP_ADDR,)

    def stop(self):
        self.transport.leaveGroup(self.SSDP_ADDR)
        self.transport.stopListening()

    def get_remote_ip(self, address):
        # Create a socket to determine what address the client should
        # use
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(address)
        iface = s.getsockname()[0]
        s.close()
        return unicode(iface)

    def datagramReceived(self, datagram, address):
        if "urn:dial-multiscreen-org:service:dial:1" in datagram and "M-SEARCH" in datagram:
            data = render(self.header).substitute(
                ip=self.get_remote_ip(address)
            )
            self.transport.write(data, address)


def LeapUPNPServer():
    sobj = SSDP()
    reactor.addSystemEventTrigger('before', 'shutdown', sobj.stop)
