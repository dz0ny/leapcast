from __future__ import unicode_literals
import argparse
import logging
import uuid


class Environment(object):
    channels = dict()
    global_status = dict()
    friendlyName = 'leapcast'
    user_agent = 'Mozilla/5.0 (CrKey - 0.9.3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/30.0.1573.2 Safari/537.36'
    chrome = '/usr/bin/chromium-browser'
    fullscreen = False
    interface = None
    uuid = None


def parse_cmd():
    parser = argparse.ArgumentParser()
    parser.add_argument('--name', help='Friendly name for this device')
    parser.add_argument('--user_agent', help='Custom user agent')
    parser.add_argument('--chrome', help='Path to Google Chrome executable')
    parser.add_argument('--fullscreen', action='store_true',
                        default=False, help='Start in full-screen mode')
    args = parser.parse_args()

    if args.name:
        Environment.friendlyName = args.name
        logging.info('Service name is %s' % Environment.friendlyName)

    if args.user_agent:
        Environment.user_agent = args.user_agent
        logging.info('User agent is %s' % args.user_agent)

    if args.chrome:
        Environment.chrome = args.chrome
        logging.info('Chrome path is %s' % args.chrome)

    if args.fullscreen:
        Environment.fullscreen = True

    generate_uuid()


def generate_uuid():
    Environment.uuid = str(uuid.uuid5(
        uuid.NAMESPACE_DNS, ('device.leapcast.%s' % Environment.friendlyName).encode('utf8')))
