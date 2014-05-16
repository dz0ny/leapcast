from __future__ import unicode_literals

import tornado.ioloop
import tornado.web
import tornado.websocket
import logging
import json
import requests
from leapcast.services.dial import DeviceHandler, ChannelFactory, SetupHandler
from leapcast.services.websocket import ServiceChannel, ReceiverChannel, ApplicationChannel, CastPlatform
from leapcast.services.leap_factory import LEAPfactory
from leapcast.environment import Environment


class LEAPserver(object):

    def start(self):
        logging.info('Starting LEAP server')
        routes = [
            (r"/ssdp/device-desc.xml", DeviceHandler),
            (r"/setup/([^\/]+)", SetupHandler),
            (r"/apps/?", DeviceHandler),
            (r"/connection", ServiceChannel),
            (r"/connection/([^\/]+)", ChannelFactory),
            (r"/receiver/([^\/]+)", ReceiverChannel),
            (r"/session/([^\/]+)", ApplicationChannel),
            (r"/system/control", CastPlatform),
        ]

        # download apps from google servers
        logging.info('Loading Config-JSON from Google-Server')
        app_dict_url = 'https://clients3.google.com/cast/chromecast/device/baseconfig'
        # load json-file
        resp = requests.get(url=app_dict_url)
        logging.info('Parsing Config-JSON')
        # parse json-file
        data = json.loads(resp.content.replace(")]}'", ""))
        # list of added apps for apps getting added manually
        added_apps = []

        if Environment.apps:
            logging.info('Reading app file: %s' % Environment.apps)
            try:
                f = open(Environment.apps)
                tmp = json.load(f)
                f.close()

                for key in tmp:
                    if key == 'applications':
                        data[key] += tmp[key]

                    else:
                        data[key] = tmp[key]
            except Exception as e:
                logging.error('Couldn\'t read app file: %s' % e)

        for app in data['applications']:
            name = app['app_id'].encode('utf-8')
            if 'url' not in app:
                logging.warning('Didn\'t add %s because it has no URL!' %
                                name)
                continue
            logging.info('Added %s app' % name)
            url = app['url']
            url = url.replace("${{URL_ENCODED_POST_DATA}}", "{{ query }}").replace(
                "${POST_DATA}", "{{ query }}")
            # this doesn't support all params yet, but seems to work with
            # youtube, chromecast and play music.
            clazz = type(name, (LEAPfactory,), {"url": url})
            routes.append(("(/apps/" + name + "|/apps/" + name + ".*)", clazz))
            added_apps.append(name)

        self.application = tornado.web.Application(routes)
        self.application.listen(8008)
        tornado.ioloop.IOLoop.instance().start()

    def shutdown(self, ):
        logging.info('Stopping DIAL server')
        tornado.ioloop.IOLoop.instance().stop()

    def sig_handler(self, sig, frame):
        tornado.ioloop.IOLoop.instance().add_callback(self.shutdown)
