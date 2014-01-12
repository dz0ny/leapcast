from __future__ import unicode_literals
import argparse
import logging
import os
import sys
import uuid

logger = logging.getLogger('Environment')


def _get_chrome_path():
    if sys.platform == 'win32':
        # First path includes fallback for Windows XP, because it doesn't have
        # LOCALAPPDATA variable.
        paths = [os.path.join(
            os.getenv(
                'LOCALAPPDATA', os.path.join(os.getenv('USERPROFILE'), 'Local Settings\\Application Data')), 'Google\\Chrome\\Application\\chrome.exe'),
            os.path.join(os.getenv('ProgramW6432', 'C:\\Program Files'),
                         'Google\\Chrome\\Application\\chrome.exe'),
            os.path.join(os.getenv('ProgramFiles(x86)', 'C:\\Program Files (x86)'), 'Google\\Chrome\\Application\\chrome.exe')]
    elif sys.platform == 'darwin':
        paths = [
            '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome']
    else:
        paths = ['/usr/bin/google-chrome',
                 '/usr/bin/chromium-browser']
    for path in paths:
        if os.path.exists(path):
            return path


class Environment(object):
    channels = dict()
    global_status = dict()
    friendlyName = 'leapcast'
    user_agent = 'Mozilla/5.0 (CrKey - 0.9.3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/30.0.1573.2 Safari/537.36'
    chrome = _get_chrome_path()
    fullscreen = False
    window_size = False
    interfaces = None
    uuid = None
    ips = []
    apps = None
    verbosity = logging.INFO


def parse_cmd():
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--debug', action='store_true',
                        default=False, dest='debug', help='Debug')
    parser.add_argument('-i', '--interface', action='append',
                        dest='interfaces',
                        help='Interface to bind to (can be specified multiple times)',
                        metavar='IPADDRESS')
    parser.add_argument('--name', help='Friendly name for this device')
    parser.add_argument('--user_agent', help='Custom user agent')
    parser.add_argument('--chrome', help='Path to Google Chrome executable')
    parser.add_argument('--fullscreen', action='store_true',
                        default=False, help='Start in full-screen mode')
    parser.add_argument('--window_size',
                        default=False,
                        help='Set the initial chrome window size. eg 1920,1080')
    parser.add_argument(
        '--ips', help='Allowed ips from which clients can connect')
    parser.add_argument('--apps', help='Add apps from JSON file')

    args = parser.parse_args()

    if args.debug:
        Environment.verbosity = logging.DEBUG
    logging.basicConfig(level=Environment.verbosity)

    if args.interfaces:
        Environment.interfaces = args.interfaces
        logger.debug('Interfaces is %s' % Environment.interfaces)

    if args.name:
        Environment.friendlyName = args.name
        logger.debug('Service name is %s' % Environment.friendlyName)

    if args.user_agent:
        Environment.user_agent = args.user_agent
        logger.debug('User agent is %s' % args.user_agent)

    if args.chrome:
        Environment.chrome = args.chrome
        logger.debug('Chrome path is %s' % args.chrome)

    if args.fullscreen:
        Environment.fullscreen = True

    if args.window_size:
        Environment.window_size = args.window_size

    if args.ips:
        Environment.ips = args.ips

    if args.apps:
        Environment.apps = args.apps

    generate_uuid()


def generate_uuid():
    Environment.uuid = str(uuid.uuid5(
        uuid.NAMESPACE_DNS, ('device.leapcast.%s' %
                             Environment.friendlyName).encode('utf8')))
