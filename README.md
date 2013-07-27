# leapcast


Simple ChromeCast emulation app.

Working:

 - Discovery (DIAL protocol http://www.dial-multiscreen.org/)
 - Youtube app

Apps:

 - YouTube uses REST, CloudProxy
 - Google music uses STOMP, CloudProxy 
 - ChromeCast local websocket and stomp, video is streamed to port 8090 using webrtc
 - Fling local websocket and stomp, launches any url

On real device enabled apps are fetched from https://clients3.google.com/cast/chromecast/device/config

TODO:

 - Play mode (via /opt/google/chrome/chrome "--app=https://www.youtube.com/tv?${POST_DATA}")
 - Remote control via STOMP and Websockets

## How to run

```
usage: app.py [-h] [--name NAME] [--user_agent USER_AGENT] [--chrome CHROME] iface

positional arguments:
  iface                 Interface you want to bind to (for example 192.168.1.22)

optional arguments:
  -h, --help              show this help message and exit
  --name NAME             Friendly name for this device
  --user_agent USER_AGENT Custom user agent
  --chrome CHROME         Path to Google Chrome executable

```

Install Google Chrome, then run

```python2 app.py ip_of_this_device --name "My super name"```
