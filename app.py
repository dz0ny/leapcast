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
import copy 

global_status = dict()
registered_apps = list()

friendlyName = "Mopidy"
user_agent ="Mozilla/5.0 (CrKey - 0.9.3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/30.0.1573.2 Safari/537.36"
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
    application_status = dict(
            name="",
            state="stopped",
            link="",
            pid=None,
            connectionSvcURL="",
            applicationContext="",
    )
    service_on = """<service xmlns="urn:dial-multiscreen-org:schemas:dial">
        <name>$name</name>
        <options allowStop="true"/>
        <activity-status xmlns="urn:chrome.google.com:cast">
            <description>Legacy</description>
            <image src="https://ssl.gstatic.com/music/fe/d52a0d1566a74f91dffa745a811ff578/favicon.ico"/>
        </activity-status>
        <servicedata xmlns="urn:chrome.google.com:cast">
            <connectionSvcURL>$connectionSvcURL</connectionSvcURL>
            <applicationContext>$applicationContext</applicationContext>
            <protocols>
                <protocol>ramp</protocol>
            </protocols>
        </servicedata>
        <state>$state</state>
        $link
    </service>
    """
    service_off = """<service xmlns="urn:dial-multiscreen-org:schemas:dial">
        <name>$name</name>
        <options allowStop="true"/>
        <state>$state</state>
        $link
    </service>
    """
    ip = None
    url = "$query"

    def get_name(self):
        return self.__class__.__name__ 

    def get_status_dict(self):
        status =copy.deepcopy(self.application_status)
        status["name"] = self.get_name()
        return status

    def prepare(self):
        self.ip = self.request.host

    def get_app_status(self):
        return global_status.get(self.get_name(), self.get_status_dict())

    def set_app_status(self, app_status):
        global global_status
        app_status["name"] = self.get_name() 
        global_status[self.get_name() ] = app_status

    def _response(self):
        self.set_header("Content-Type", "application/xml; charset=UTF-8")
        self.set_header("Cache-control", "no-cache, must-revalidate, no-store")
        
        self.finish(self._toXML(self.get_app_status()))

    @tornado.web.asynchronous
    def post(self, sec):
        """Start app"""
        self.set_status(201)
        self.set_header("Location", self._getLocation(self.get_name()))

        status = self.get_status_dict()
        status["state"]="running"
        status["link"]="""<link rel="run" href="run"/>"""
        status["pid"]=self.launch(self.request.body)
        status["connectionSvcURL"]="http://%s/ramp/%s" % (self.ip, self.get_name() )
        
        self.set_app_status(status)
        self._response()

    @tornado.web.asynchronous
    def get(self, sec):
        """Status of an app"""

        if self.get_app_status()["pid"]:
            # app crashed or closed
            if self.get_app_status()["pid"].poll() is not None:

                status = self.get_status_dict()
                status["state"]="stopped"
                status["link"]=""
                status["pid"]=None
                
                self.set_app_status(status)
        self._response()

    @tornado.web.asynchronous
    def delete(self, sec):
        """Close app"""
        self.destroy(self.get_app_status()["pid"])
        status = self.get_status_dict()
        status["state"]="stopped"
        status["link"]=""
        status["pid"]=None
        
        self.set_app_status(status)
        self._response()

    def _getLocation(self, app):
        return "http://%s/apps/%s/run" % (self.ip, app )

    def launch(self, data):
        appurl = string.Template(self.url).substitute(query=data)
        command_line ="""%s --incognito --kiosk --user-agent="%s"  --app="%s" """  % (chrome, user_agent, appurl.replace("&idle=windowclose",""))
        args = shlex.split(command_line)
        return subprocess.Popen(args)

    def destroy(self, pid):
        if pid is not None:
            pid.terminate()

    def _toXML(self, data):
        if data["pid"] is not None:
            return string.Template(dedent(self.service_on)).substitute(data)
        else:
            return string.Template(dedent(self.service_off)).substitute(data)

    @classmethod
    def toInfo(cls):
        data = copy.deepcopy(cls.application_status)
        data["name"] =  cls.__name__
        data = global_status.get(cls.__name__, data)
        if data["pid"] is not None:
            return string.Template(dedent(cls.service_on)).substitute(data)
        else:
            return string.Template(dedent(cls.service_off)).substitute(data)
class ChromeCast(LEAP):
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
    url = "https://www.gstatic.com/eureka/html/gcp.html"

class Fling(LEAP):
    url = "https://www.gstatic.com/eureka/html/gcp.html"

class TicTacToe(LEAP):
    url = "http://www.gstatic.com/eureka/sample/tictactoe/tictactoe.html"

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
            <UDN>uuid:3e1cc7c0-f4f3-11e2-b778-0800200c9a66</UDN>
            <serviceList>
                <service>
                    <serviceType>urn:schemas-upnp-org:service:dail:1</serviceType>
                    <serviceId>urn:upnp-org:serviceId:dail</serviceId>
                    <controlURL>/ssdp/notfound</controlURL>
                    <eventSubURL>/ssdp/notfound</eventSubURL>
                    <SCPDURL>/ssdp/notfound</SCPDURL>
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
        apps = []
        for app in registered_apps:
            apps.append(app.toInfo())
        self.write(string.Template(dedent(self.device)).substitute(dict(services="\n".join(apps), friendlyName=friendlyName, path=path )))


class WS(tornado.websocket.WebSocketHandler):
    def open(self, app=None):
        self.app = app
        logging.info("%s opened %s" % (self.__class__.__name__, self.request.uri) )
        self.cmd_id = 0

    def on_message(self, message):
        cmd = json.loads(message)
        self.on_cmd(cmd)

    def on_cmd(self, cmd):
        print(cmd)

    def on_close(self):
        logging.info("%s closed %s" % (self.__class__.__name__, self.request.uri) )

    def reply(self, msg):
        msg["cmd_id"] = self.cmd_id
        self.write_message((json.dumps(msg)))
        self.cmd_id += 1


class CastChannel(WS):
    """
    RAMP over WebSocket.  It acts like proxy between receiver app(1st screen) and remote app(2nd screen)
    """
    def on_cmd(self, cmd):
        if cmd["type"] == "REGISTER":
            self.info = cmd
            self.new_request()
        if cmd["type"] == "CHANNELRESPONSE":
            self.new_chanell()

    def new_chanell(self):
        ws = "ws://localhost:8008/ramp/%s" % self.info["name"]
        logging.info("New channel for app %s %s" %(self.info["name"], ws ))
        self.reply({"type":"NEWCHANNEL" , "senderId":"1", "requestId": "123456", "URL": ws})

    def new_request(self):
        logging.info("New CHANNELREQUEST for app %s" %(self.info["name"] ))
        self.reply({"type":"CHANNELREQUEST", "requestId": "123456", "senderId":"1"})

class CastPlatform(WS):
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

class CastRAMP(WS):
    """
    Remote proxy over WebSocket.

    """
    def reply(self, msg):
        self.write_message((json.dumps(msg)))

    def on_cmd(self, cmd):
        if cmd[0] == "cm":
            self.on_cm_command(cmd[1])
        if cmd[0] == "ramp":
            self.on_ramp_command(cmd[1])


    def on_cm_command(self, cmd):
        print cmd
        self.reply(['cm', {'type': 'pong'}])

    def on_ramp_command(self, cmd):
        print cmd

class HTTPThread(threading.Thread):
   
    def register_app(self, app):
        global registered_apps
        name = app.__name__
        registered_apps.append(app)
        return (r"(/apps/" + name+ "|/apps/" + name+ "/run)", app)

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

            (r"/connection", CastChannel),
            (r"/ramp/([^\/]+)", CastRAMP),
            (r"/system/control", CastPlatform),
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
