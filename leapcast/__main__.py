#!/usr/bin/env python
# -*- coding: utf8 -*-

from __future__ import unicode_literals

import signal
import logging
import sys
from os import environ


from leapcast.environment import parse_cmd, Environment
from leapcast.services.leap import LEAPserver
from leapcast.utils.avahi import Zeroconf

logger = logging.getLogger('Leapcast')


def main():
    parse_cmd()

    if sys.platform == 'darwin' and environ.get('TMUX') is not None:
        logger.error('Running Chrome inside tmux on OS X might cause problems.'
                     ' Please start leapcast outside tmux.')
        sys.exit(1)

    def shutdown(signum, frame):
        leap_server.sig_handler(signum, frame)
        avahi_service.unpublish()

    signal.signal(signal.SIGTERM, shutdown)
    signal.signal(signal.SIGINT, shutdown)

    avahi_service = Zeroconf(
        Environment.friendlyName, 8008, host='::')
    avahi_service.publish()

    leap_server = LEAPserver()
    leap_server.start()

if __name__ == "__main__":
    main()
