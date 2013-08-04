from __future__ import unicode_literals

from leapcast.environment import Environment
from leapcast.services.websocket import App
from leapcast.utils import render
import tornado.web


class DeviceHandler(tornado.web.RequestHandler):

    '''
    Holds info about device
    '''

    device = '''<?xml version="1.0" encoding="utf-8"?>
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
    </root>'''

    def get(self):
        if self.request.uri == "/apps":
            for app, astatus in Environment.global_status.items():
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
            self.write(render(self.device).substitute(
                dict(
                    friendlyName=Environment.friendlyName,
                    uuid=Environment.uuid,
                    path="http://%s" % self.request.host)
            )
            )


class ChannelFactory(tornado.web.RequestHandler):

    '''
    Creates Websocket Channel. This is requested by 2nd screen application
    '''
    @tornado.web.asynchronous
    def post(self, app=None):
        self.app = App.get_instance(app)
        self.set_header(
            "Access-Control-Allow-Method", "POST, OPTIONS")
        self.set_header("Access-Control-Allow-Headers", "Content-Type")
        self.set_header("Content-Type", "application/json")
        ## TODO: Use information from REGISTER packet
        ## TODO: return url based on channel property
        ## TODO: defer request until receiver connects
        self.finish(
            '{"URL":"ws://%s/session/%s?%s","pingInterval":3}' % (
            self.request.host, app, self.app.get_apps_count())
        )
