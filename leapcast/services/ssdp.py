# -*- coding: utf8 -*-

from __future__ import unicode_literals

import socket
import logging
from SocketServer import DatagramRequestHandler

from leapcast.utils import render, MulticastServer
from leapcast.environment import Environment


class SSDPHandler(DatagramRequestHandler):
    header = '''\
    HTTP/1.1 200 OK\r
    LOCATION: http://{{ ip }}:8008/ssdp/device-desc.xml\r
    CACHE-CONTROL: max-age=1800\r
    CONFIGID.UPNP.ORG: 7337\r
    BOOTID.UPNP.ORG: 7337\r
    USN: uuid:{{ uuid }}\r
    ST: urn:dial-multiscreen-org:service:dial:1\r
    \r
    '''

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
        if "urn:dial-multiscreen-org:service:dial:1" in datagram and "M-SEARCH" in datagram:
            data = render(self.header).generate(
                ip=self.get_remote_ip(address),
                uuid=Environment.uuid
            )
            self.reply(data, address)


class SSDPserver(object):
    SSDP_ADDR = '239.255.255.250'
    SSDP_PORT = 1900

    def start(self, interfaces):
        logging.info('Starting SSDP server')
        self.server = MulticastServer(
            (self.SSDP_ADDR, self.SSDP_PORT), SSDPHandler,
            interfaces=interfaces)
        self.server.start()

    def shutdown(self):
        logging.info('Stopping SSDP server')
        self.server.server_close()
        self.server.stop()