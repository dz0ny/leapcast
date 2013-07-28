#!/usr/bin/python

# Python program that emulates ChromeCast device

from twisted.internet import reactor
from twisted.internet.protocol import DatagramProtocol
import tornado.ioloop
import tornado.web
import tornado.websocket
import threading
import string
import argparse
import signal
import logging
from textwrap import dedent
import shlex, subprocess
import json

status = dict()

friendlyName = "Mopidy"
user_agent ="Mozilla/5.0 (CrKey - 0.0.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/30.0.1573.2 Safari/537.36"
chrome = "/opt/google/chrome/chrome"

class SSDP(DatagramProtocol):
    SSDP_ADDR = '239.255.255.250'
    SSDP_PORT = 1900
    MS = """HTTP/1.1 200 OK\r
LOCATION: http://$ip:8008/ssdp/device-desc.xml\r
CACHE-CONTROL: max-age=1800\r
CONFIGID.UPNP.ORG: 7337\r
BOOTID.UPNP.ORG: 7337\r
USN: uuid:3e1cc7c0-f4f3-11e2-b778-0800200c9a66::urn:dial-multiscreen-org:service:dial:1\r
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
            data =string.Template(dedent(self.MS)).substitute(ip=self.iface)
            self.transport.write(data, address)

class LEAP(tornado.web.RequestHandler):

    service =  """<service xmlns="urn:dial-multiscreen-org:schemas:dial">
        <name>$name</name>
        <options allowStop="true"/>
        <state>$state</state>
        $link
    </service>
    """
    ip = None
    url = "$query"

    def prepare(self):
        global status
        if self.__class__.__name__ not in status:
            status[self.__class__.__name__ ] = dict(name=self.__class__.__name__ , state="stopped", link="", pid=None)
        self.ip = self.request.host

    def get_app_status(self):
        return status[self.__class__.__name__ ]

    def set_app_status(self, app_status):
        global status
        app_status["name"] = self.__class__.__name__ 
        status[self.__class__.__name__ ] = app_status

    def _response(self):
        self.set_header("Content-Type", "application/xml; charset=UTF-8")
        self.set_header("Cache-control", "no-cache, must-revalidate, no-store")
        self.finish(self._toXML(self.get_app_status()))

    @tornado.web.asynchronous
    def post(self, sec):
        """Start app"""
        self.set_status(201)
        self.set_header("Location", self._getLocation(self.__class__.__name__))
        pid = self.launch(self.request.body)
        self.set_app_status(dict(state="running", link="""<link rel="run" href="run"/>""", pid=pid))
        self._response()

    @tornado.web.asynchronous
    def get(self, sec):
        """Status of an app"""

        if self.get_app_status()["pid"]:
            # app crashed or closed
            if self.get_app_status()["pid"].poll() is not None:
                self.set_app_status(dict(name=self.__class__.__name__ , state="stopped", link="", pid=None))
        self._response()

    @tornado.web.asynchronous
    def delete(self, sec):
        """Close app"""
        self.destroy(self.get_app_status()["pid"])
        self.set_app_status(dict(name=self.__class__.__name__ , state="stopped", link="", pid=None))
        self._response()

    def _getLocation(self, app):
        return "http://%s/apps/%s/run" % (self.ip, app )

    def launch(self, data):
        appurl = string.Template(self.url).substitute(query=data)
        command_line ="""%s --incognito --kiosk --user-agent="%s"  "%s" """  % (chrome, user_agent, appurl)
        print(command_line)
        args = shlex.split(command_line)
        return subprocess.Popen(args)

    def destroy(self, pid):
        pid.terminate()

    def _toXML(self, data):
        return string.Template(dedent(self.service)).substitute(data)

    @classmethod
    def toInfo(cls):
        global status
        if cls.__name__ not in status:
            status[cls.__name__ ] = dict(name=cls.__name__ , state="stopped", link="", pid=None)
        return string.Template(dedent(cls.service)).substitute(status[cls.__name__])

class ChromeCast(LEAP):
    service = """<service xmlns="urn:chrome.google.com:cast">
        <name>ChromeCast</name>
        <options allowStop="true"/>
        <activity-status>
            <description>Experimental Mopidy sink</description>
            <image src="http://www.mopidy.com/media/images/penguin_speakers.jpg"/>
        </activity-status>
        <servicedata>
            <protocols>
                <protocol>video_playback</protocol>
                <protocol>audio_playback</protocol>
            </protocols>
        </servicedata>
        <state>$state</state>
        $link
    </service>
    """
    url = "https://www.gstatic.com/cv/receiver.html?$query"

class YouTube(LEAP):
    url = "https://www.youtube.com/tv?$query"

class PlayMovies(LEAP):
    url = "https://play.google.com/video/avi/eureka?$query"

class GoogleMusic(LEAP):
    url = "https://play.google.com/music/cast/player"

class GoogleCastSampleApp(LEAP):
    url = "http://anzymrcvr.appspot.com/receiver/anzymrcvr.html"


class GoogleCastPlayer(LEAP):
    url = "http://anzymrcvr.appspot.com/receiver/anzymrcvr.html"

class Fling(LEAP):
    url = "http://anzymrcvr.appspot.com/receiver/anzymrcvr.html"

class DeviceHandler(tornado.web.RequestHandler):

    device = """<?xml version="1.0" encoding="utf-8"?>
    <root xmlns="urn:schemas-upnp-org:device-1-0" xmlns:r="urn:restful-tv-org:schemas:upnp-dd">
      <specVersion>
        <major>1</major>
        <minor>0</minor>
      </specVersion>
      <URLBase>$path</URLBase>
      <device>
        <deviceType>urn:schemas-upnp-org:device:tvdevice:1</deviceType>
        <friendlyName>$friendlyName</friendlyName>
        <manufacturer>Google Inc.</manufacturer>
        <modelName>ChromeCast</modelName>
        <UDN>uuid:3e1cc7c0-f4f3-11e2-b778-0800200c9a66</UDN>
        
        <serviceList>
        <service>
          <serviceType>urn:schemas-upnp-org:service:tvcontrol:1</serviceType>
          <serviceId>urn:upnp-org:serviceId:tvcontrol1</serviceId>
          <controlURL>/upnp/control/tvcontrol1</controlURL>
          <eventSubURL>/upnp/event/tvcontrol1</eventSubURL>
          <SCPDURL>/tvcontrolSCPD.xml</SCPDURL>
        </service>
        $services
        </serviceList>
      </device>
    </root>"""

    def get(self):
        path = "http://%s/apps" % self.request.host
        self.add_header("Application-URL",path)
        self.set_header("Content-Type", "application/xml; charset=UTF-8")
        self.set_header("Cache-control", "no-cache")
        gservice = "\n".join( [
            ChromeCast.toInfo(),
            YouTube.toInfo(),
            PlayMovies.toInfo(),
            GoogleMusic.toInfo(),
            GoogleCastSampleApp.toInfo(),
            GoogleCastPlayer.toInfo(),
            Fling.toInfo(),
        ])
        self.write(string.Template(dedent(self.device)).substitute(dict(services=gservice, friendlyName=friendlyName, path=path )))

class WebSocketCast(tornado.websocket.WebSocketHandler):

    def open(self):
        logging.info("WebSocket opened")

    def on_message(self, message):
        cmd = json.loads(message)
        print(cmd)
        if cmd["type"] == "REGISTER":
            self.new_request()

    def on_close(self):
        logging.info("WebSocket opened")

    def new_chanell(self):
        self.write_message((json.dumps({"type":"NEWCHANNEL"})))

    def new_request(self):
        self.write_message((json.dumps({"type":"CHANNELREQUEST", "requestId": "123456"})))

class HTTPThread(threading.Thread):
   
    def run(self):

        self.application = tornado.web.Application([
            (r"/ssdp/device-desc.xml", DeviceHandler),

            (r"/apps", DeviceHandler),
            (r"(/apps/ChromeCast|/apps/ChromeCast/run)", ChromeCast),
            (r"(/apps/YouTube|/apps/YouTube/run)", YouTube),
            (r"(/apps/PlayMovies|/apps/PlayMovies/run)", PlayMovies),
            (r"(/apps/GoogleMusic|/apps/GoogleMusic/run)", GoogleMusic),
            (r"(/apps/GoogleCastSampleApp|/apps/GoogleCastSampleApp/run)", GoogleCastSampleApp),
            (r"(/apps/GoogleCastPlayer|/apps/GoogleCastPlayer/run)", GoogleCastPlayer),
            (r"(/apps/Fling|/apps/Fling/run)", Fling),

            (r"/connection", WebSocketCast),
            (r"/system/control", WebSocketCast),
        ])
        self.application.listen(8008)
        tornado.ioloop.IOLoop.instance().start()
    
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
    parser.add_argument('iface', help='Interface you want to bind to (for example 192.168.1.22)')
    parser.add_argument('--name', help='Friendly name for this device')
    parser.add_argument('--user_agent', help='Custom user agent')
    parser.add_argument('--chrome', help='Path to Google Chrome executable')
    args = parser.parse_args()

    if args.name:
        friendlyName = args.name
        logging.info("Service name is %s" % friendlyName)

    if args.user_agent:
        user_agent = args.user_agent
        logging.info("User agent is %s" % user_agent)

    if args.chrome:
        chrome = args.chrome
        logging.info("Chrome path is %s" % chrome)

    server = HTTPThread()
    server.start()

    signal.signal(signal.SIGTERM, server.sig_handler)
    signal.signal(signal.SIGINT, server.sig_handler)

    def LeapUPNPServer():
        logging.info("Listening on %s" % args.iface)
        sobj = SSDP(args.iface)
        reactor.addSystemEventTrigger('before', 'shutdown', sobj.stop)

    reactor.callWhenRunning(LeapUPNPServer)
    reactor.run()
