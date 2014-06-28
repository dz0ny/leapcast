# -*- coding: utf8 -*-

from __future__ import unicode_literals
import socket
import struct
import logging
from SocketServer import DatagramRequestHandler
from time import sleep

from dnslib import PTR, QTYPE, RR, DNSRecord, SRV, A, RD, DNSHeader, \
    DNSLabel

from leapcast.environment import Environment
from leapcast.services.ssdp import MulticastServer


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


def RRlist2bitmap(lst):
    """
    Encode a list of integers representing Resource Records to a bitmap field
    used in the NSEC Resource Record.
    """
    # RFC 4034, 4.1.2. The Type Bit Maps Field

    import math

    bitmap = b""
    lst = list(set(lst))
    lst.sort()

    lst = filter(lambda x: x <= 65535, lst)
    lst = map(lambda x: abs(x), lst)

    # number of window blocks
    max_window_blocks = int(math.ceil(lst[-1] / 256.))
    min_window_blocks = int(math.floor(lst[0] / 256.))
    if min_window_blocks == max_window_blocks:
        max_window_blocks += 1

    for wb in xrange(min_window_blocks, max_window_blocks + 1):
        # First, filter out RR not encoded in the current window block
        # i.e. keep everything between 256*wb <= 256*(wb+1)
        rrlist = filter(lambda x: 256 * wb <= x and x < 256 * (wb + 1), lst)
        rrlist.sort()
        if rrlist == []:
            continue

        # Compute the number of bytes used to store the bitmap
        if rrlist[-1] == 0:  # only one element in the list
            bytes = 1
        else:
            max = rrlist[-1] - 256 * wb
            bytes = int(math.ceil(max / 8)) + 1  # use at least 1 byte
        if bytes > 32:  # Don't encode more than 256 bits / values
            bytes = 32

        bitmap += struct.pack("B", wb)
        bitmap += struct.pack("B", bytes)

        # Generate the bitmap
        for tmp in xrange(bytes):
            v = 0
            # Remove out of range Ressource Records
            tmp_rrlist = filter(lambda
                                    x: 256 * wb + 8 * tmp <= x and x < 256 * wb + 8 * tmp + 8,
                                rrlist)
            if not tmp_rrlist == []:
                # 1. rescale to fit into 8 bits
                tmp_rrlist = map(lambda x: (x - 256 * wb) - (tmp * 8),
                                 tmp_rrlist)
                # 2. x gives the bit position ; compute the corresponding value
                tmp_rrlist = map(lambda x: 2 ** (7 - x), tmp_rrlist)
                # 3. sum everything
                v = reduce(lambda x, y: x + y, tmp_rrlist)
            bitmap += struct.pack("B", v)

    return bitmap


class NSEC(RD):
    def __init__(self, target=None, types=[]):
        self.bitmap = RRlist2bitmap(types)
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
        buffer.encode_name(self.target)
        buffer.append(self.bitmap)


    def __repr__(self):
        return "%s" % self.target


    attrs = 'target'


def mDNSResponse(name, ip, ttl):
    """
    Create mDns response packet

    :param name: string Friendly name
    :param ip: string address of device
    :param ttl: Time to store response
    :return: DNSHeader object
    """

    if ttl == 0:
        ttl_secondary = 0
    else:
        ttl_secondary = 120

    res = mDNSHeader()
    res.add_answer(RR(
        "_googlecast._tcp.local",
        QTYPE.PTR,
        rdata=PTR("%s._googlecast._tcp.local" % name),
        ttl=ttl
    ))
    # TODO: Use generated id
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
        ttl=ttl_secondary
    ))
    res.add_ar(RR(
        "%s.local" % name,
        QTYPE.A,
        rdata=A(ip),
        ttl=ttl_secondary
    ))
    res.add_ar(RR(
        "%s._googlecast._tcp.local" % name,
        QTYPE.NSEC,
        rdata=NSEC(
            target="%s._googlecast._tcp.local" % name,
            types=[QTYPE.TXT, QTYPE.SRV]
        ),
        ttl=ttl
    ))
    res.add_ar(RR(
        "%s.local" % name,
        QTYPE.NSEC,
        rdata=NSEC(
            target="%s.local" % name,
            types=[QTYPE.A]
        ),
        ttl=ttl_secondary
    ))
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
            logging.info('MDNS Response for %s %s' % address)
            res = mDNSResponse(name, ip, 3600)

            self.reply(res, address)  # unicast response
            sleep(1)  # avoid multicast collision with avahi and others
            self.reply(res, ('224.0.0.251', 5353))


class MDNSserver(object):
    MDNS_ADDR = '224.0.0.251'
    MDNS_PORT = 5353
    server = None

    def start(self, interfaces):
        logging.info('Starting MDNS server')
        self.server = MulticastServer(
            (self.MDNS_ADDR, self.MDNS_PORT),
            MDNSHandler,
            interfaces=interfaces
        )
        self.server.start()
        # TODO: Advertise itself on wire

    def shutdown(self):
        logging.info('Stopping MDNS server')
        # TODO: Flush all network caches with ttl 0
        self.server.server_close()
        self.server.stop()