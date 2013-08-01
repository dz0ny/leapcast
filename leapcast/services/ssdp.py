import logging
import socket
import string
from textwrap import dedent
import uuid
from leapcast.environment import Environment
from twisted.internet import reactor
from twisted.internet.protocol import DatagramProtocol


class SSDP(DatagramProtocol):
    SSDP_ADDR = '239.255.255.250'
    SSDP_PORT = 1900
    MS = """HTTP/1.1 200 OK\r
LOCATION: http://$ip:8008/ssdp/device-desc.xml\r
CACHE-CONTROL: max-age=1800\r
CONFIGID.UPNP.ORG: 7337\r
BOOTID.UPNP.ORG: 7337\r
USN: uuid:$uuid\r
ST: urn:dial-multiscreen-org:service:dial:1\r
\r
"""

    def __init__(self, iface):
        self.iface = iface
        self.transport = reactor.listenMulticast(
            self.SSDP_PORT, self, listenMultiple=True)
        self.transport.setLoopbackMode(1)
        self.transport.joinGroup(self.SSDP_ADDR, interface=iface)

    def stop(self):
        self.transport.leaveGroup(self.SSDP_ADDR, interface=self.iface)
        self.transport.stopListening()

    def datagramReceived(self, datagram, address):
        if "urn:dial-multiscreen-org:service:dial:1" in datagram and "M-SEARCH" in datagram:
            iface = self.iface
            if not iface:
                # Create a socket to determine what address the client should
                # use
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.connect(address)
                iface = s.getsockname()[0]
                s.close()
            data = string.Template(dedent(self.MS)).substitute(
                ip=iface, uuid=uuid.uuid5(uuid.NAMESPACE_DNS, Environment.friendlyName))
            self.transport.write(data, address)


def LeapUPNPServer():
    logging.info("Listening on %s" % (Environment.interface or 'all'))
    sobj = SSDP(Environment.interface)
    reactor.addSystemEventTrigger('before', 'shutdown', sobj.stop)