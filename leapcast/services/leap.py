from __future__ import unicode_literals

import shlex
import subprocess
import copy
import logging
import tempfile
import shutil

from leapcast.environment import Environment
import tornado.ioloop
import tornado.web
import tornado.websocket
from leapcast.services.websocket import App
from leapcast.utils import render


class Browser(object):

    def __init__(self, appurl):
        if not Environment.fullscreen:
            appurl = '--app="%s"' % appurl
        command_line = '''%s --incognito --no-first-run --kiosk --user-agent="%s"  %s''' % (
            Environment.chrome, Environment.user_agent, appurl)
        args = shlex.split(command_line)
        self.tmpdir = tempfile.mkdtemp(prefix="leapcast-")
        args.append('--user-data-dir=%s' % self.tmpdir)
        self.pid = subprocess.Popen(args)

    def destroy(self):
        self.pid.terminate()
        self.pid.wait()
        shutil.rmtree(self.tmpdir)

    def is_running(self):
        return self.pid.poll() is None

    def __bool__(self):
        return self.is_running()


class LEAP(tornado.web.RequestHandler):
    application_status = dict(
        name="",
        state="stopped",
        link="",
        browser=None,
        connectionSvcURL="",
        protocols="",
        app=None
    )
    service = '''<?xml version="1.0" encoding="UTF-8"?>
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
    '''

    ip = None
    url = "$query"
    supported_protocols = ["ramp"]

    @property
    def protocols(self):
        return '\n '.join('<protocol>{0}</protocol>'.format(w) for w in self.supported_protocols)

    def get_name(self):
        return self.__class__.__name__

    def get_status_dict(self):
        status = copy.deepcopy(self.application_status)
        status["name"] = self.get_name()
        return status

    def prepare(self):
        self.ip = self.request.host

    def get_app_status(self):
        return Environment.global_status.get(self.get_name(), self.get_status_dict())

    def set_app_status(self, app_status):

        app_status["name"] = self.get_name()
        Environment.global_status[self.get_name()] = app_status

    def _response(self):
        self.set_header("Content-Type", "application/xml")
        self.set_header(
            "Access-Control-Allow-Method", "GET, POST, DELETE, OPTIONS")
        self.set_header("Access-Control-Expose-Headers", "Location")
        self.set_header("Cache-control", "no-cache, must-revalidate, no-store")
        self.finish(self._toXML(self.get_app_status()))

    @tornado.web.asynchronous
    def post(self, sec):
        '''Start app'''
        self.clear()
        self.set_status(201)
        self.set_header("Location", self._getLocation(self.get_name()))
        status = self.get_app_status()
        if status["browser"] is None:
            status["state"] = "running"
            status["link"] = '''<link rel="run" href="web-1"/>'''
            appurl = render(self.url).substitute(query=self.request.body)
            status["browser"] = Browser(appurl)
            status["connectionSvcURL"] = "http://%s/connection/%s" % (
                self.ip, self.get_name())
            status["protocols"] = self.protocols
            status["app"] = App.get_instance(sec)

        self.set_app_status(status)
        self.finish()

    @tornado.web.asynchronous
    def get(self, sec):
        '''Status of an app'''
        self.clear()
        browser = self.get_app_status()["browser"]
        if not browser:
            logging.debug("App crashed or closed")
            # app crashed or closed
            status = self.get_status_dict()
            status["state"] = "stopped"
            status["link"] = ""
            status["browser"] = None
            self.set_app_status(status)

        self._response()

    @tornado.web.asynchronous
    def delete(self, sec):
        '''Close app'''
        self.clear()
        browser = self.get_app_status()["browser"]
        if browser is not None:
            browser.destroy()
        else:
            logging.warning("App already closed in destroy()")
        status = self.get_status_dict()
        status["state"] = "stopped"
        status["link"] = ""
        status["browser"] = None

        self.set_app_status(status)
        self._response()

    def _getLocation(self, app):
        return "http://%s/apps/%s/web-1" % (self.ip, app)

    def _toXML(self, data):
        return render(self.service).substitute(data)

    @classmethod
    def toInfo(cls):
        data = copy.deepcopy(cls.application_status)
        data["name"] = cls.__name__
        data = Environment.global_status.get(cls.__name__, data)
        return render(cls.service).substitute(data)
