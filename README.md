# leapcast
![Google Music](http://screencloud.net//img/screenshots/3c17671ad386247d7dbd2f7395c4df77.png "Google Music")

Simple ChromeCast emulation app.

Working:

 - Discovery (DIAL protocol http://www.dial-multiscreen.org/)
 - Youtube
 - Google Music
 - TicTacToe

On real device enabled apps are fetched from https://clients3.google.com/cast/chromecast/device/config


## How to run

```
usage: app.py [-h] [--iface IFACE] [--name NAME] [--user_agent USER_AGENT]
              [--chrome CHROME] [--fullscreen]

optional arguments:
  -h, --help            show this help message and exit
  --iface IFACE         Interface you want to bind to (for example
                        192.168.1.22)
  --name NAME           Friendly name for this device
  --user_agent USER_AGENT
                        Custom user agent
  --chrome CHROME       Path to Google Chrome executable
  --fullscreen          Start in full-screen mode

```

Install Google Chrome, twisted and tornado then run

```./app.py --name "My super name"```
