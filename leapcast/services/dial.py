from __future__ import unicode_literals

import leapcast
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
        <URLBase>{{ path }}</URLBase>
        <device>
            <deviceType>urn:schemas-upnp-org:device:dail:1</deviceType>
            <friendlyName>{{ friendlyName }}</friendlyName>
            <manufacturer>Google Inc.</manufacturer>
            <modelName>Eureka Dongle</modelName>
            <UDN>uuid:{{ uuid }}</UDN>
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
        if Environment.ips and self.request.remote_ip not in Environment.ips:
            raise tornado.web.HTTPError(403)
        global_app = True
        for app, astatus in Environment.global_status.items():
            if astatus["state"] == "running":
                self.redirect("/apps/%s" % app)
                global_app = False
        if global_app:
            self.redirect("/apps/00000000-0000-0000-0000-000000000000")


class SetupHandler(tornado.web.RequestHandler):
    '''
    Holds info about device setup and status
    '''

    status = '''{
        "build_version":"{{ buildVersion}}",
        "connected":true,
        "detail":{
            "locale":{"display_string":"English (United States)"},
            "timezone":{"display_string":"America/Los Angeles",offset:-480}
        },
        "has_update":false,
        "hdmi_control":true,
        "hotspot_bssid":"FA:8F:CA:3A:0C:D0",
        "locale": "en_US",
        "mac_address":"00:00:00:00:00:00",
        "name":"{{ name }}",
        "noise_level":-90,
        "opt_in":{"crash":true,"device_id":false,"stats":true},
        "public_key":"MIIBCgKCAQEAyoaWlKNT6W5+/cJXEpIfeGvogtJ1DghEUs2PmHkX3n4bByfmMRDYjuhcb97vd8N3HFe5sld6QSc+FJz7TSGp/700e6nrkbGj9abwvobey/IrLbHTPLtPy/ceUnwmAXczkhay32auKTaM5ZYjwcHZkaU9XuOQVIPpyLF1yQerFChugCpQ+bvIoJnTkoZAuV1A1Vp4qf3nn4Ll9Bi0R4HJrGNmOKUEjKP7H1aCLSqj13FgJ2s2g20CCD8307Otq8n5fR+9/c01dtKgQacupysA+4LVyk4npFn5cXlzkkNPadcKskARtb9COTP2jBWcowDwjKSBokAgi/es/5gDhZm4dwIDAQAB",
        "release_track":"stable-channel",
        "setup_state":60,
        {% raw signData %}
        "signal_level":-50,
        "ssdp_udn":"82c5cb87-27b4-2a9a-d4e1-5811f2b1992c",
        "ssid":"{{ friendlyName }}",
        "timezone":"America/Los_Angeles",
        "uptime":0.0,
        "version":4,
        "wpa_configured":true,
        "wpa_state":10
    }'''

    # Chromium OS's network_DestinationVerification.py has a verify test that
    # shows that it is possible to verify signed_data by:
    #   echo "<signed_data>" | base64 -d | openssl rsautl -verify -inkey <certificate> -certin -asn1parse
    # The signed string should match:
    #   echo -n "<name>,<ssdp_udn>,<hotspot_bssid>,<public_key>,<nonce>" | openssl sha1 -binary | hd

    sign_data = '''
        "sign": {
            "certificate":"-----BEGIN CERTIFICATE-----\\nMIIDqzCCApOgAwIBAgIEUf6McjANBgkqhkiG9w0BAQUFADB9MQswCQYDVQQGEwJV\\nUzETMBEGA1UECAwKQ2FsaWZvcm5pYTEWMBQGA1UEBwwNTW91bnRhaW4gVmlldzET\\nMBEGA1UECgwKR29vZ2xlIEluYzESMBAGA1UECwwJR29vZ2xlIFRWMRgwFgYDVQQD\\nDA9FdXJla2EgR2VuMSBJQ0EwHhcNMTMwODA0MTcxNjM0WhcNMzMwNzMwMTcxNjM0\\nWjCBgDETMBEGA1UEChMKR29vZ2xlIEluYzETMBEGA1UECBMKQ2FsaWZvcm5pYTEL\\nMAkGA1UEBhMCVVMxFjAUBgNVBAcTDU1vdW50YWluIFZpZXcxEjAQBgNVBAsTCUdv\\nb2dsZSBUVjEbMBkGA1UEAxMSWktCVjIgRkE4RkNBM0EwQ0QwMIIBIjANBgkqhkiG\\n9w0BAQEFAAOCAQ8AMIIBCgKCAQEA+HGhzj+XEwhUT7W4FbaR8M2sNxCF0VrlWsw6\\nSkFHOINt6t+4B11Q7TSfz1yzrMhUSQvaE2gP2F/h3LD03rCnnE4avonZYTBr/U/E\\nJZYDjEtOClFmBmqNf6ZEE8bxF/nsit1e5XicO0OJHSmRlvibbrmC2rnFwj/cEDpm\\na1hdqpRQkeG0ceb9qbvvpxBq4MBsomzzbSq2nl7dQFBpxDd2jm7g+4EC7KqWmkWt\\n3XgX++0qk4qFlbc/+ySqheYYddU0eeExvg93WkTRr5m6ZuaTQn7LOO9IiR8PwSnz\\nxQmuirtAc50089T1oyV7ANZlNtj2oW2XjKUvxA3n+x8jCqAwfwIDAQABoy8wLTAJ\\nBgNVHRMEAjAAMAsGA1UdDwQEAwIHgDATBgNVHSUEDDAKBggrBgEFBQcDAjANBgkq\\nhkiG9w0BAQUFAAOCAQEAXmXinb7zoutrwCw+3SQVGbQycnMpWz1hDRS+BZ04QCm0\\naxneva74Snptjasnw3eEW9Yb1N8diLlrUWkT5Q9l8AA/W4R3B873lPTzWhobXFCq\\nIhrkTDBSOtx/bQj7Sy/npmoj6glYlKKANqTCDhjHvykOLrUUeCjltYAy3i8km+4b\\nTxjfB6D3IIGB3kvb1L4TmvgSuXDhkz0qx2qR/bM6vGShnNRCQo6oR4hAMFlvDlXR\\nhRfuibIJwtbA2cLUyG/UjgQwJEPrlOT6ZyLRHWMjiROKcqv3kqatBfNyIjkVD4uH\\nc+WK9DlJnI9bLy46qYRVbzhhDJUkfZVtDKiUbvz3bg==\\n-----END CERTIFICATE-----\\n",
            "nonce": "Aw4o0/sbVr537Kdrw9YotiXxCLIaiRrDkHeHrOpih3U=",
            "signed_data": "fcTwn3K4I/ccok1MeZ5/nkM0pI5v4SrTv3Q4ppOQtVL5ii3qitNo+NLhY+DM9zmnP6ndNMZbkyIEyMm7LjganoDoE+o0e0/r4TyGEGLxYlfWSzf+Z3cSdNe4+MyHx/7z02E0/3lLsOFuOEPSgR26JFtyhDLCJ9Y8Cpl3GZMUqm4toaTNaIbhNMR9Bwjkz4ozKXzFl9dF5FTU6N48KeUP/3CuYqgm04BVUGxg+DbBmTidRnZE4eGdt9ICJht9ArUNQDL2UdRYVY2sfgLmF29exTaSrVkBZb/MsbDxN5nYpF1uE7IhzJnT5yFM9pmUOIKKTfeVaLVLGgoWd+pjEbOv+Q=="
        },
    '''

    timezones = '''[
        {"timezone":"America/Los_Angeles","display_string":"America/Los Angeles","offset":-480}
    ]'''
    locales = '''[
        {"locale":"en_US","display_string":"English (United States)"}
    ]'''
    wifi_networks = '''[
        {"bssid":"00:00:00:00:00:00","signal_level":-60,"ssid":"leapcast","wpa_auth":7,"wpa_cipher":4}
    ]'''

    def get(self, module=None):
        if Environment.ips and self.request.remote_ip not in Environment.ips:
            raise tornado.web.HTTPError(403)

        if module == "eureka_info":
            self.set_header(
                "Access-Control-Allow-Headers", "Content-Type")
            self.set_header(
                "Access-Control-Allow-Origin", "https://cast.google.com")
            self.set_header("Content-Type", "application/json")
            if 'sign' in self.request.query:
                name = 'Chromecast8991'
                signData = self.sign_data
            else:
                name = Environment.friendlyName
                signData = ''
            self.write(render(self.status).generate(
                name=name,
                friendlyName=Environment.friendlyName,
                buildVersion='leapcast %s' % leapcast.__version__,
                signData=signData,
                uuid=Environment.uuid)
            )
        elif module == "supported_timezones":
            self.set_header("Content-Type", "application/json")
            self.write(self.timezones)
        elif module == "supported_locales":
            self.set_header("Content-Type", "application/json")
            self.write(self.locales)
        elif module == "scan_results":
            self.set_header("Content-Type", "application/json")
            self.write(self.wifi_networks)
        else:
            raise tornado.web.HTTPError(404)

    def post(self, module=None):
        if ((len(Environment.ips) == 0) | (
            self.request.remote_ip in Environment.ips)):
            if module == "scan_wifi":
                pass
            elif module == "set_eureka_info":
                pass
            elif module == "connect_wifi":
                pass
            else:
                raise tornado.web.HTTPError(404)
        else:
            raise tornado.web.HTTPError(404)


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
        self.finish(
            '{"URL":"ws://%s/session/%s?%s","pingInterval":3}' % (
                self.request.host, app, self.app.get_apps_count())
        )
        self.app.create_application_channel(self.request.body)
