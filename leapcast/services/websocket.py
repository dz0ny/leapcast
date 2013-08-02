# -*- coding: utf8 -*-

from __future__ import unicode_literals
from collections import deque
import json
import logging
from leapcast.environment import Environment
import tornado.web


class App(object):
    '''
    Used to relay messages between app Environment.channels
    '''
    name = ""
    remotes = list()
    receivers = list()
    rec_queue = list()
    control_channel = list()
    info = None

    @classmethod
    def get_instance(cls, app):

        if app in Environment.channels:
            return Environment.channels[app]
        else:
            instance = App()
            instance.name = app
            Environment.channels[app] = instance
            return instance

    @classmethod
    def stop(cls, app):

        if app.name in Environment.channels:
            del Environment.channels[app.name]

    def set_control_channel(self, ch):

        logging.info("Channel for app %s set", ch)
        self.control_channel.append(ch)

    def get_control_channel(self):
        logging.info("Channel for app %s set", self.control_channel[0])
        return self.control_channel[0]

    def get_apps_count(self):
        return len(self.remotes)

    def get_recv_count(self):
        return len(self.receivers)

    def add_remote(self, remote):
        self.remotes.append(remote)

    def add_receiver(self, receiver):
        self.receivers.append(receiver)
        self.rec_queue.append(deque())

    def get_deque(self, instance):
        try:
            id = self.receivers.index(instance)
            return self.rec_queue[id]
        except Exception:
            queue = deque()
            self.rec_queue.append(queue)
            return queue

    def get_app_channel(self, receiver):
        try:
            return self.remotes[self.receivers.index(receiver)]
        except Exception:
            return None

    def get_recv_channel(self, app):
        try:
            return self.receivers[self.remotes.index(app)]
        except Exception:
            return None


class ServiceChannel(tornado.websocket.WebSocketHandler):
    '''
    ws /connection
    From 1st screen app
    '''

    def open(self, app=None):
        self.app = App.get_instance(app)
        self.app.set_control_channel(self)

    def on_message(self, message):
        cmd = json.loads(message)
        if cmd["type"] == "REGISTER":
            self.app.info = cmd
            self.new_request()
        if cmd["type"] == "CHANNELRESPONSE":
            self.new_channel()

    def reply(self, msg):
        self.write_message((json.dumps(msg)))

    def new_channel(self):

        ws = "ws://localhost:8008/receiver/%s" % self.app.info["name"]
        self.reply(
            {
                "type": "NEWCHANNEL",
                "senderId": self.app.get_recv_count(),
                "requestId": self.app.get_apps_count(),
                "URL": ws
            }
        )

    def new_request(self):
        logging.info("New CHANNELREQUEST for app %s" % (self.app.info["name"]))
        self.reply(
            {
                "type": "CHANNELREQUEST",
                "senderId": self.app.get_recv_count(),
                "requestId": self.app.get_apps_count(),
            }
        )

    def on_close(self):
        App.stop(self.app)


class WSC(tornado.websocket.WebSocketHandler):
    def open(self, app=None):
        self.app = App.get_instance(app)
        self.cname = self.__class__.__name__

        if self.cname == "ReceiverChannel":
            self.app.add_receiver(self)
            queue = self.app.get_deque(self)
            if len(queue) > 0:
                for i in xrange(0, len(queue)):
                    self.write_message(queue.pop())

        if self.cname == "ApplicationChannel":
            self.app.add_remote(self)

        logging.info("%s opened %s" %
                     (self.cname, self.request.uri))

    def on_message(self, message):
        logging.debug("%s: %s" % (self.cname, message))

        if self.cname == "ReceiverChannel":
            channel = self.app.get_app_channel(self)
            if channel:
                channel.write_message(message)

        if self.cname == "ApplicationChannel":
            channel = self.app.get_recv_channel(self)
            if channel:
                channel.write_message(message)
            else:
                queue = self.app.get_deque(self)
                queue.append(message)

    def on_close(self):
        if self.cname == "ReceiverChannel":
            self.app.receivers.remove(self)
        if self.cname == "ApplicationChannel":
            self.app.remotes.remove(self)

        logging.info("%s closed %s" %
                     (self.cname, self.request.uri))


class ReceiverChannel(WSC):
    '''
    ws /receiver/$app
    From 1nd screen app
    '''


class ApplicationChannel(WSC):
    '''
    ws /session/$app
    From 2nd screen app
    '''


class CastPlatform(tornado.websocket.WebSocketHandler):
    '''
    Remote control over WebSocket.

    Commands are:
    {u'type': u'GET_VOLUME', u'cmd_id': 1}
    {u'type': u'GET_MUTED', u'cmd_id': 2}
    {u'type': u'VOLUME_CHANGED', u'cmd_id': 3}
    {u'type': u'SET_VOLUME', u'cmd_id': 4}
    {u'type': u'SET_MUTED', u'cmd_id': 5}

    Device control:

    '''

    def on_message(self, message):
        pass
