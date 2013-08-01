import string
from textwrap import dedent
import uuid
from __future__ import unicode_literals

from leapcast.environment import Environment
from leapcast.services.websocket import App
import tornado.web


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
            self.write(string.Template(dedent(self.device)).substitute(
                dict(
                    uuid=uuid.uuid5(
                        uuid.NAMESPACE_DNS, Environment.friendlyName),
                    friendlyName=Environment.friendlyName,
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
        self.finish(
            '{"URL":"ws://192.168.3.22:8008/session/%s?%s","pingInterval":3}' % (
                app, self.app.get_apps_count())
        )
