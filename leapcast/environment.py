from __future__ import unicode_literals
import argparse
import logging


class Environment(object):
    channels = dict()
    global_status = dict()
    friendlyName = "Mopidy"
    user_agent = "Mozilla/5.0 (CrKey - 0.9.3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/30.0.1573.2 Safari/537.36"
    chrome = "/opt/google/chrome/chrome"
    fullscreen = False
    interface = None


def parse_cmd():
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
        Environment.interface = args.iface
        logging.info("Service name is %s" % args.iface)

    if args.name:
        Environment.friendlyName = args.name
        logging.info("Service name is %s" % args.name)

    if args.user_agent:
        Environment.user_agent = args.user_agent
        logging.info("User agent is %s" % args.user_agent)

    if args.chrome:
        Environment.chrome = args.chrome
        logging.info("Chrome path is %s" % args.chrome)

    if args.fullscreen:
        Environment.fullscreen = True
