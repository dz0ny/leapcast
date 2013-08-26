# -*- coding: utf8 -*-

from __future__ import unicode_literals
from tornado.template import Template
from textwrap import dedent
import threading


def render(template):
    return Template(dedent(template))


class ControlMixin(object):

    def __init__(self, handler, poll_interval):
        self._thread = None
        self.poll_interval = poll_interval
        self._handler = handler

    def start(self):
        self._thread = t = threading.Thread(target=self.serve_forever,
                                            args=(self.poll_interval,))
        t.setDaemon(True)
        t.start()

    def stop(self):
        self.shutdown()
        self._thread.join()
        self._thread = None
