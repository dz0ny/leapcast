#!/usr/bin/env python
# -*- coding: utf8 -*-

from __future__ import unicode_literals
import threading
import signal
import logging

from twisted.internet import reactor
import tornado.ioloop
import tornado.web
import tornado.websocket
from leapcast.environment import parse_cmd
from leapcast.apps.default import *
from leapcast.services.rest import *
from leapcast.services.ssdp import LeapUPNPServer
from leapcast.services.websocket import *


class HTTPThread(object):
    def run(self):
        self.application = tornado.web.Application([
            (r"/ssdp/device-desc.xml", DeviceHandler),
            (r"/apps", DeviceHandler),

            self.register_app(ChromeCast),
            self.register_app(YouTube),
            self.register_app(PlayMovies),
            self.register_app(GoogleMusic),
            self.register_app(GoogleCastSampleApp),
            self.register_app(GoogleCastPlayer),
            self.register_app(TicTacToe),
            self.register_app(Fling),

            (r"/connection", ServiceChannel),
            (r"/connection/([^\/]+)", ChannelFactory),
            (r"/receiver/([^\/]+)", ReceiverChannel),
            (r"/session/([^\/]+)", ApplicationChannel),
            (r"/system/control", CastPlatform),
        ])
        self.application.listen(8008)
        tornado.ioloop.IOLoop.instance().start()

    def start(self):
        threading.Thread(target=self.run).start()

    def shutdown(self, ):
        logging.info('Stopping HTTP server')
        reactor.callFromThread(reactor.stop)
        logging.info('Stopping DIAL server')
        tornado.ioloop.IOLoop.instance().stop()

    def register_app(self, app):
        name = app.__name__
        return (r"(/apps/" + name + "|/apps/" + name + ".*)", app)

    def sig_handler(self, sig, frame):
        tornado.ioloop.IOLoop.instance().add_callback(self.shutdown)


def main():
    logging.basicConfig(level=logging.INFO)
    parse_cmd()

    server = HTTPThread()
    server.start()
    signal.signal(signal.SIGTERM, server.sig_handler)
    signal.signal(signal.SIGINT, server.sig_handler)

    reactor.callWhenRunning(LeapUPNPServer)
    reactor.run()


if __name__ == "__main__":
    main()
