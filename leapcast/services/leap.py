from __future__ import unicode_literals

import tornado.ioloop
import tornado.web
import tornado.websocket
import logging
from leapcast.apps.default import *
from leapcast.services.rest import *
from leapcast.services.websocket import *


class LEAPserver(object):

    def start(self):
        logging.info('Starting LEAP server')
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

    def shutdown(self, ):
        logging.info('Stopping DIAL server')
        tornado.ioloop.IOLoop.instance().stop()

    def register_app(self, app):
        name = app.__name__
        logging.debug('Added %s app' % name)
        return (r"(/apps/" + name + "|/apps/" + name + ".*)", app)

    def sig_handler(self, sig, frame):
        tornado.ioloop.IOLoop.instance().add_callback(self.shutdown)
