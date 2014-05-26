# -*- coding: utf8 -*-

from __future__ import unicode_literals
import contextlib
import socket
import struct
import operator
import logging
from SocketServer import ThreadingUDPServer, DatagramRequestHandler
from time import sleep

from dnslib import PTR, QTYPE, RR, DNSRecord, SRV, A, RD, DNSHeader, DNSLabel

from leapcast.environment import Environment
from leapcast.utils import ControlMixin


def mDNSHeader():
    header = DNSHeader(id=0, ra=1, aa=1, qr=1)
    return DNSRecord(header)


class MTXT(RD):
    def __init__(self, txts=[]):
        self.multiple_texts = txts

    def pack(self, buffer):
        for txt in self.multiple_texts:
            buffer.append(struct.pack("!B", len(txt)))
            buffer.append(str(txt))

    def toZone(self):
        return '"%s"' % repr(self)

    def __repr__(self):
        # Pyyhon 2/3 hack
        return ' '.join(self.multiple_texts)

class NSEC(RD):

    def __init__(self, target=None):

        self.target = target

    def set_target(self, target):
        if isinstance(target, DNSLabel):
            self._target = target
        else:
            self._target = DNSLabel(target)

    def get_target(self):
        return self._target

    target = property(get_target, set_target)

    def pack(self, buffer):
        #buffer.pack("!HHH",self.priority,self.weight,self.port)
        buffer.encode_name(self.target)

    def __repr__(self):
        return "%s" % self.target

    attrs = 'target'

def GetInterfaceAddress(if_name):
    import fcntl  # late import as this is only supported on Unix platforms.

    SIOCGIFADDR = 0x8915
    with contextlib.closing(
            socket.socket(socket.AF_INET, socket.SOCK_DGRAM)) as s:
        return fcntl.ioctl(s.fileno(), SIOCGIFADDR,
                           struct.pack(b'256s', if_name[:15]))[20:24]


class MulticastServer(ControlMixin, ThreadingUDPServer):
    allow_reuse_address = True

    def __init__(self, addr, handler, poll_interval=0.5,
                 bind_and_activate=True, interfaces=None):
        ThreadingUDPServer.__init__(self, ('', addr[1]),
                                    handler,
                                    bind_and_activate)
        ControlMixin.__init__(self, handler, poll_interval)
        self._multicast_address = addr
        self._listen_interfaces = interfaces
        self.setLoopbackMode(1)  # localhost
        self.setTTL(2)  # localhost and local network
        self.handle_membership(socket.IP_ADD_MEMBERSHIP)

    def setLoopbackMode(self, mode):
        mode = struct.pack("b", operator.truth(mode))
        self.socket.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_LOOP,
                               mode)

    def server_bind(self):
        try:
            if hasattr(socket, "SO_REUSEADDR"):
                self.socket.setsockopt(
                    socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        except Exception as e:
            logging.log(e)
        try:
            if hasattr(socket, "SO_REUSEPORT"):
                self.socket.setsockopt(
                    socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        except Exception as e:
            logging.log(e)
        ThreadingUDPServer.server_bind(self)

    def handle_membership(self, cmd):
        if self._listen_interfaces is None:
            mreq = struct.pack(
                str("4sI"), socket.inet_aton(self._multicast_address[0]),
                socket.INADDR_ANY)
            self.socket.setsockopt(socket.IPPROTO_IP,
                                   cmd, mreq)
        else:
            for interface in self._listen_interfaces:
                try:
                    if_addr = socket.inet_aton(interface)
                except socket.error:
                    if_addr = GetInterfaceAddress(interface)
                mreq = socket.inet_aton(self._multicast_address[0]) + if_addr
                self.socket.setsockopt(socket.IPPROTO_IP,
                                       cmd, mreq)

    def setTTL(self, ttl):
        ttl = struct.pack("B", ttl)
        self.socket.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl)

    def server_close(self):
        self.handle_membership(socket.IP_DROP_MEMBERSHIP)


def mDNSResponse(name, ip, ttl):
    """
    Create mDns response packet

    :param name: string Friendly name
    :param ip: string address of device
    :param ttl: Time to store response
    :return: DNSHeader object
    """
    res = mDNSHeader()
    res.add_answer(RR(
        "_googlecast._tcp.local",
        QTYPE.PTR,
        rdata=PTR("%s._googlecast._tcp.local" % name),
        ttl=ttl
    ))
    res.add_ar(RR(
        "%s._googlecast._tcp.local" % name,
        QTYPE.TXT,
        rdata=MTXT([
            'id=99e46e880f89a46ae627f2e75278cb46',
            've=02',
            'md=Chromecast',
            'ic=/setup/icon.png',
        ]),
        ttl=ttl
    ))
    res.add_ar(RR(
        "%s._googlecast._tcp.local" % name,
        QTYPE.SRV,
        rdata=SRV(port=8009, target='%s.local' % name),
        ttl=120
    ))
    res.add_ar(RR(
        "%s.local" % name,
        QTYPE.A,
        rdata=A(ip),
        ttl=120
    ))
    # res.add_ar(RR(
    #     "%s._googlecast._tcp.local" % name,
    #     QTYPE.NSEC,
    #     rdata=NSEC(target="%s._googlecast._tcp.local" % name)
    # ), ttl=ttl)
    # res.add_ar(RR(
    #     "%s.local" % name,
    #     QTYPE.NSEC,
    #     rdata=NSEC(target="%s.local" % name)
    # ), ttl=120)
    return res.pack()


class MDNSHandler(DatagramRequestHandler):
    def handle(self):
        data = self.request[0].strip()
        self.datagramReceived(data, self.client_address)

    def reply(self, data, address):
        socket = self.request[1]
        socket.sendto(data, address)

    def get_remote_ip(self, address):
        # Create a socket to determine what address the client should
        # use
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(address)
        iface = s.getsockname()[0]
        s.close()
        return unicode(iface)

    def datagramReceived(self, datagram, address):
        if not len(datagram) > 0:
            return
        try:
            req = DNSRecord.parse(datagram)
            query = req.get_q()
        except Exception:
            return

        if '_googlecast._tcp.local' in str(query.get_qname()) and 12 == query \
                .qtype and query.qclass == 1:
            ip = self.get_remote_ip(address)
            name = Environment.friendlyName
            res = mDNSResponse(name, ip, 3600)
            sleep(1)  # avoid multicast collision with avahi and others
            self.reply(res, ('224.0.0.251', 5353))
        else:
            print(req.get_q().get_qname())


class MDNSserver(object):
    MDNS_ADDR = '224.0.0.251'
    MDNS_PORT = 5353
    server = None

    def start(self, interfaces):
        logging.info('Starting MDNS server')
        self.server = MulticastServer(
            (self.MDNS_ADDR, self.MDNS_PORT), MDNSHandler,
            interfaces=interfaces)
        self.server.start()
        # TODO: Advertise itself on wire

    def shutdown(self):
        logging.info('Stopping MDNS server')
        # TODO: Flush all network caches with ttl 0
        self.server.server_close()
        self.server.stop()