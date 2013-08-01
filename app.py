#!/usr/bin/python

# Python program that emulates ChromeCast device

from twisted.internet import reactor
from twisted.internet.protocol import DatagramProtocol
import tornado.ioloop
import tornado.web
import tornado.websocket
import socket
import threading
import string
import argparse
import signal
import logging
from textwrap import dedent
import shlex
import subprocess
import json
import copy
import uuid
from collections import deque


class Enviroment(object):
    channels = dict()
    global_status = dict()
    friendlyName = "Mopidy"
    user_agent = "Mozilla/5.0 (CrKey - 0.9.3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/30.0.1573.2 Safari/537.36"
    chrome = "/opt/google/chrome/chrome"
    fullscreen = False


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
                ip=iface, uuid=uuid.uuid5(uuid.NAMESPACE_DNS, Enviroment.friendlyName))
            self.transport.write(data, address)


class LEAP(tornado.web.RequestHandler):
    application_status = dict(
        name="",
        state="stopped",
        link="",
        pid=None,
        connectionSvcURL="",
        protocols="",
        app=None
    )
    service = """<?xml version="1.0" encoding="UTF-8"?>
    <service xmlns="urn:dial-multiscreen-org:schemas:dial">
        <name>$name</name>
        <options allowStop="true"/>
        <activity-status xmlns="urn:chrome.google.com:cast">
            <description>Legacy</description>
        </activity-status>
        <servicedata xmlns="urn:chrome.google.com:cast">
            <connectionSvcURL>$connectionSvcURL</connectionSvcURL>
            <protocols>$protocols</protocols>
        </servicedata>
        <state>$state</state>
        $link
    </service>
    """

    ip = None
    url = "$query"
    protocols = ""

    def get_name(self):
        return self.__class__.__name__

    def get_status_dict(self):
        status = copy.deepcopy(self.application_status)
        status["name"] = self.get_name()
        return status

    def prepare(self):
        self.ip = self.request.host

    def get_app_status(self):
        return Enviroment.global_status.get(self.get_name(), self.get_status_dict())

    def set_app_status(self, app_status):

        app_status["name"] = self.get_name()
        Enviroment.global_status[self.get_name()] = app_status

    def _response(self):
        self.set_header("Content-Type", "application/xml")
        self.set_header(
            "Access-Control-Allow-Method", "GET, POST, DELETE, OPTIONS")
        self.set_header("Access-Control-Expose-Headers", "Location")
        self.set_header("Cache-control", "no-cache, must-revalidate, no-store")
        self.finish(self._toXML(self.get_app_status()))

    @tornado.web.asynchronous
    def post(self, sec):
        """Start app"""
        self.clear()
        self.set_status(201)
        self.set_header("Location", self._getLocation(self.get_name()))
        status = self.get_app_status()
        if status["pid"] is None:
            status["state"] = "running"
            status["link"] = """<link rel="run" href="web-1"/>"""
            status["pid"] = self.launch(self.request.body)
            status["connectionSvcURL"] = "http://%s/connection/%s" % (
                self.ip, self.get_name())
            status["protocols"] = self.protocols
            status["app"] = App.get_instance(sec)

        self.set_app_status(status)
        self.finish()

    @tornado.web.asynchronous
    def get(self, sec):
        """Status of an app"""
        self.clear()
        if self.get_app_status()["pid"]:
            # app crashed or closed
            if self.get_app_status()["pid"].poll() is not None:

                status = self.get_status_dict()
                status["state"] = "stopped"
                status["link"] = ""
                status["pid"] = None

                self.set_app_status(status)
        self._response()

    @tornado.web.asynchronous
    def delete(self, sec):
        """Close app"""
        self.clear()
        self.destroy(self.get_app_status()["pid"])
        status = self.get_status_dict()
        status["state"] = "stopped"
        status["link"] = ""
        status["pid"] = None

        self.set_app_status(status)
        self._response()

    def _getLocation(self, app):
        return "http://%s/apps/%s/web-1" % (self.ip, app)

    def launch(self, data):
        appurl = string.Template(self.url).substitute(query=data)
        if not Enviroment.fullscreen:
            appurl = '--app="%s"' % appurl
        command_line = """%s --incognito --no-first-run --kiosk --user-agent="%s"  %s"""  % (
            Enviroment.chrome, Enviroment.user_agent, appurl)
        args = shlex.split(command_line)
        return subprocess.Popen(args)

    def destroy(self, pid):
        if pid is not None:
            pid.terminate()

    def _toXML(self, data):
        return string.Template(dedent(self.service)).substitute(data)

    @classmethod
    def toInfo(cls):
        data = copy.deepcopy(cls.application_status)
        data["name"] = cls.__name__
        data = Enviroment.global_status.get(cls.__name__, data)
        return string.Template(dedent(cls.service)).substitute(data)


class ChromeCast(LEAP):
    url = "https://www.gstatic.com/cv/receiver.html?$query"
    protocols = "<protocol>ramp</protocol>"


class YouTube(LEAP):
    url = "https://www.youtube.com/tv?$query"
    protocols = "<protocol>ramp</protocol>"


class PlayMovies(LEAP):
    url = "https://play.google.com/video/avi/eureka?$query"
    protocols = "<protocol>ramp</protocol><protocol>play-movies</protocol>"


class GoogleMusic(LEAP):
    url = "https://play.google.com/music/cast/player"
    protocols = "<protocol>ramp</protocol>"


class GoogleCastSampleApp(LEAP):
    url = "http://anzymrcvr.appspot.com/receiver/anzymrcvr.html"
    protocols = "<protocol>ramp</protocol>"


class GoogleCastPlayer(LEAP):
    url = "https://www.gstatic.com/eureka/html/gcp.html"
    protocols = "<protocol>ramp</protocol>"


class Fling(LEAP):
    url = "https://www.gstatic.com/eureka/html/gcp.html"
    protocols = "<protocol>ramp</protocol>"


class TicTacToe(LEAP):
    url = "http://www.gstatic.com/eureka/sample/tictactoe/tictactoe.html"
    protocols = "<protocol>com.google.chromecast.demo.tictactoe</protocol>"


class DeviceHandler(tornado.web.RequestHandler):

    device = """<?xml version="1.0" encoding="utf-8"?>
    <root xmlns="urn:schemas-upnp-org:device-1-0" xmlns:r="urn:restful-tv-org:schemas:upnp-dd">
        <specVersion>
        <major>1</major>
        <minor>0</minor>
        </specVersion>
        <URLBase>$path</URLBase>
        <device>
            <deviceType>urn:schemas-upnp-org:device:dail:1</deviceType>
            <friendlyName>$friendlyName</friendlyName>
            <manufacturer>Google Inc.</manufacturer>
            <modelName>Eureka Dongle</modelName>
            <UDN>uuid:$uuid</UDN>
            <serviceList>
                <service>
                    <serviceType>urn:schemas-upnp-org:service:dail:1</serviceType>
                    <serviceId>urn:upnp-org:serviceId:dail</serviceId>
                    <controlURL>/ssdp/notfound</controlURL>
                    <eventSubURL>/ssdp/notfound</eventSubURL>
                    <SCPDURL>/ssdp/notfound</SCPDURL>
                </service>
            </serviceList>
        </device>
    </root>"""

    def get(self):
        if self.request.uri == "/apps":
            for app, astatus in Enviroment.global_status.items():
                if astatus["state"] == "running":
                    self.redirect("/apps/%s" % app)
            self.set_status(204)
            self.set_header(
                "Access-Control-Allow-Method", "GET, POST, DELETE, OPTIONS")
            self.set_header("Access-Control-Expose-Headers", "Location")
        else:
            self.set_header(
                "Access-Control-Allow-Method", "GET, POST, DELETE, OPTIONS")
            self.set_header("Access-Control-Expose-Headers", "Location")
            self.add_header(
                "Application-URL", "http://%s/apps" % self.request.host)
            self.set_header("Content-Type", "application/xml")
            self.write(string.Template(dedent(self.device)).substitute(
                dict(
                    uuid=uuid.uuid5(uuid.NAMESPACE_DNS, Enviroment.friendlyName),
                    friendlyName=Enviroment.friendlyName,
                    path="http://%s" % self.request.host)
            )
            )


class ChannelFactory(tornado.web.RequestHandler):

    @tornado.web.asynchronous
    def post(self, app=None):

        self.app = App.get_instance(app)
        self.set_header(
            "Access-Control-Allow-Method", "POST, OPTIONS")
        self.set_header("Access-Control-Allow-Headers", "Content-Type")
        self.set_header("Content-Type", "application/json")
        if self.app.get_recv_count() >= 1:
            self.app.get_control_channel().new_channel()
        self.finish(
            '{"URL":"ws://192.168.3.22:8008/session/%s?%s","pingInterval":3}' % (
                app, self.app.get_apps_count())
        )


class CastPlatform(tornado.websocket.WebSocketHandler):

    """
    Remote control over WebSocket.

    Commands are:
    {u'type': u'GET_VOLUME', u'cmd_id': 1}
    {u'type': u'GET_MUTED', u'cmd_id': 2}
    {u'type': u'VOLUME_CHANGED', u'cmd_id': 3}
    {u'type': u'SET_VOLUME', u'cmd_id': 4}
    {u'type': u'SET_MUTED', u'cmd_id': 5}

    Device control:

    """

    def on_message(self, message):
        print


class App(object):

    """
    Used to relay messages between app Enviroment.channels
    """
    name = ""
    remotes = list()
    receivers = list()
    rec_queue = list()
    control_channel = list()
    info = None

    @classmethod
    def get_instance(cls, app):

        if Enviroment.channels.has_key(app):
            return Enviroment.channels[app]
        else:
            instance = App()
            instance.name = app
            Enviroment.channels[app] = instance
            return instance

    @classmethod
    def stop(cls, app):

        if Enviroment.channels.has_key(app.name):
            del Enviroment.channels[app.name]

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

    """
    ws /connection
    From 1st screen app
    """

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

    """
    ws /receiver/$app
    From 1nd screen app
    """


class ApplicationChannel(WSC):

    """
    ws /session/$app
    From 2nd screen app
    """


class HTTPThread(object):

    def __init__(self, iface):
        self.iface = iface

    def register_app(self, app):
        name = app.__name__
        return (r"(/apps/" + name + "|/apps/" + name + "/run)", app)

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
        self.application.listen(8008, address=self.iface)
        tornado.ioloop.IOLoop.instance().start()

    def start(self):
        threading.Thread(target=self.run).start()

    def shutdown(self, ):
        logging.info('Stopping HTTP server')
        reactor.callFromThread(reactor.stop)
        logging.info('Stopping DIAL server')
        tornado.ioloop.IOLoop.instance().stop()

    def sig_handler(self, sig, frame):
        tornado.ioloop.IOLoop.instance().add_callback(self.shutdown)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--iface', help='Interface you want to bind to (for example 192.168.1.22)', default='')
    parser.add_argument('--name', help='Friendly name for this device')
    parser.add_argument('--user_agent', help='Custom user agent')
    parser.add_argument('--chrome', help='Path to Google Chrome executable')
    parser.add_argument('--fullscreen', action='store_true',
                        default=False, help='Start in full-screen mode')
    args = parser.parse_args()

    if args.name:
        Enviroment.friendlyName = args.name
        logging.info("Service name is %s" % args.name)

    if args.user_agent:
        Enviroment.user_agent = args.user_agent
        logging.info("User agent is %s" % args.user_agent)

    if args.chrome:
        Enviroment.chrome = args.chrome
        logging.info("Chrome path is %s" % args.chrome)

    if args.fullscreen:
        Enviroment.fullscreen = True

    server = HTTPThread(args.iface)
    server.start()

    signal.signal(signal.SIGTERM, server.sig_handler)
    signal.signal(signal.SIGINT, server.sig_handler)

    def LeapUPNPServer():
        logging.info("Listening on %s" % (args.iface or 'all'))
        sobj = SSDP(args.iface)
        reactor.addSystemEventTrigger('before', 'shutdown', sobj.stop)

    reactor.callWhenRunning(LeapUPNPServer)
    reactor.run()
