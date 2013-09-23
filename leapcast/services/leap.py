from __future__ import unicode_literals

import tornado.ioloop
import tornado.web
import tornado.websocket
import logging
from leapcast.apps.default import *
from leapcast.services.dial import DeviceHandler, ChannelFactory
from leapcast.services.websocket import ServiceChannel, ReceiverChannel, ApplicationChannel, CastPlatform
from leapcast.services.leap_factory import LEAPfactory


class LEAPserver(object):

    def start(self):
        logging.info('Starting LEAP server')
        routes = [
            (r"/ssdp/device-desc.xml", DeviceHandler),
            (r"/apps", DeviceHandler),
            (r"/connection", ServiceChannel),
            (r"/connection/([^\/]+)", ChannelFactory),
            (r"/receiver/([^\/]+)", ReceiverChannel),
            (r"/session/([^\/]+)", ApplicationChannel),
            (r"/system/control", CastPlatform),
        ]

        #add registread apps
        for app in LEAPfactory.get_subclasses():
            name = app.__name__
            logging.info('Added %s app' % name)
            routes.append((
                r"(/apps/" + name + "|/apps/" + name + ".*)", app))

        self.application = tornado.web.Application(routes)
        self.application.listen(8008)
        tornado.ioloop.IOLoop.instance().start()

    def shutdown(self, ):
        logging.info('Stopping DIAL server')
        tornado.ioloop.IOLoop.instance().stop()

    def sig_handler(self, sig, frame):
        tornado.ioloop.IOLoop.instance().add_callback(self.shutdown)
