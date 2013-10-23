# leapcast
[![Flattr this git repo](http://api.flattr.com/button/flattr-badge-large.png)](https://flattr.com/submit/auto?user_id=dz0ny&url=https://github.com/dz0ny/leapcast&title=Leapcast&language=&tags=github&category=software) 
![Google Music](http://screencloud.net//img/screenshots/3c17671ad386247d7dbd2f7395c4df77.png "Google Music")

Simple ChromeCast emulation app.

Working:

 - Discovery (DIAL protocol http://www.dial-multiscreen.org/)
 - Youtube
 - Google Music
 - TicTacToe
 - ChromeCast

On real device enabled apps are fetched from https://clients3.google.com/cast/chromecast/device/config .
Bugs in ChromeCast SDK are listed at https://code.google.com/p/google-cast-sdk/issues/list?can=2&q=&sort=priority&colspec=ID%20Type%20Status%20Priority%20Milestone%20Owner%20Summary 

Some known bugs in ChromeCast SDK:
 
 - Discovery fails on some devices with multiple unactive network interfaces 
 - Scanning crashes device or app with ConcurrentModificationException 

## How to install

### Simple

Clone this directory, then run ```python setup.py develop``` or ```pip install https://github.com/dz0ny/leapcast/archive/master.zip```

### Better

```
git clone https://github.com/dz0ny/leapcast.git
cd ./leapcast
sudo apt-get install virtualenvwrapper python-pip python-twisted-web python2.7-dev
mkvirtualenv leapcast
pip install .
```

#### Windows

For those on Windows(tm) follow this guide https://gist.github.com/eyecatchup/6219118 or https://plus.google.com/100317092290545434762/posts/8RjWfMXxje8

```
usage: leapcast [-h] [-d] [--name NAME] [--user_agent USER_AGENT]
                [--chrome CHROME] [--fullscreen]

optional arguments:
  -h, --help            show this help message and exit
  -d                    Debug
  --name NAME           Friendly name for this device
  --user_agent USER_AGENT
                        Custom user agent
  --chrome CHROME       Path to Google Chrome executable
  --fullscreen          Start in full-screen mode
  --window_size         Force the initial window size (eg 1920,1080)

```


[![Bitdeli Badge](https://d2weczhvl823v0.cloudfront.net/dz0ny/leapcast/trend.png)](https://bitdeli.com/free "Bitdeli Badge")

