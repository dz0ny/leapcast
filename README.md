# leapcast


Simple ChromeCast emulation app.

Working:

 - Discovery (DIAL protocol http://www.dial-multiscreen.org/)
 - Youtube app

Apps:

 - YouTube uses REST + CloudProxy or REST + RAMP
 - Google music uses RAMP 

On real device enabled apps are fetched from https://clients3.google.com/cast/chromecast/device/config

TODO:

 - Remote control via RAMP and Websockets

## Websocket Channel creation

1st screen device:
    - GET /connection (ws)


2nd screen device: 

    - GET /ssdp/device-desc.xml HTTP/1.1
    - HTTP/1.1 200 OK
    - POST /apps/APP HTTP/1.1
    - HTTP/1.1 201 Created and $connectionSvcURL
    - POST $connectionSvcURL < create channel
    - HTTP/1.1 200 OK < Session URL
    - GET /session/app (ws)

## How to run

```
usage: app.py [-h] [--name NAME] [--user_agent USER_AGENT] [--chrome CHROME]
               [--fullscreen]
               iface

positional arguments:
  iface Interface you want to bind to (for example 192.168.1.22)

optional arguments:
  -h, --help              show this help message and exit
  --name NAME             Friendly name for this device
  --user_agent USER_AGENT Custom user agent
  --chrome CHROME         Path to Google Chrome executable
  --fullscreen            Start in full-screen mode


```

Install Google Chrome, twisted and tornado then run

```python2 app.py ip_of_this_device --name "My super name"```
