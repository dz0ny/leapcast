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

## What is RAMP(remote media access proxy?)

- 1st screnn device(chromecast) acts like proxy betweeen two browser/app sessions 
- 2nd screen device creates app, then waits for screenId
- 1st screen device after app starts issues REGISTER RAMP packet
- 1st > 2nd Issues CHANNELREQUEST with requestId which is the same as that in screenId in DIAL xml
- 2nd screen device connects via websockets using screenId and isses LOAD, INFO, PLAY, STOP, VOLUME
- 1st screen responds accordingly

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
