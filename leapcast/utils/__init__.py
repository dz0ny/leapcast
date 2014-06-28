from __future__ import unicode_literals
from SocketServer import ThreadingUDPServer
import logging
import socket
import struct
import operator
import contextlib
from textwrap import dedent
import threading

from tornado.template import Template


def render(template):
    return Template(dedent(template))


class ControlMixin(object):
    def __init__(self, handler, poll_interval):
        self._thread = None
        self.poll_interval = poll_interval
        self._handler = handler

    def start(self):
        self._thread = t = threading.Thread(target=self.serve_forever,
                                            args=(self.poll_interval,))
        t.setDaemon(True)
        t.start()

    def stop(self):
        self.shutdown()
        self._thread.join()
        self._thread = None


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
        self.setTTL(255)  # all networks
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


def get_remote_ip(address):
    # Create a socket to determine what address the client should
    # use
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(address)
    iface = s.getsockname()[0]
    s.close()
    return unicode(iface)
