# leapcast
[![Flattr this git repo](http://api.flattr.com/button/flattr-badge-large.png)](https://flattr.com/submit/auto?user_id=dz0ny&url=https://github.com/dz0ny/leapcast&title=Leapcast&language=&tags=github&category=software)
[![Build Status](https://travis-ci.org/dz0ny/leapcast.png?branch=master)](https://travis-ci.org/dz0ny/leapcast)
[![Gitter chat](https://badges.gitter.im/dz0ny/leapcast.png)](https://gitter.im/dz0ny/leapcast)

# Chromecast API v2 (develop branch)

In order to get it working again, we need to:

- [x] Implement MDNS discovery (done)
- [ ] Implement Chrome Cast channel on port 8009 (https://code.google.com/p/chromium/codesearch#chromium/src/chrome/browser/extensions/api/cast_channel/&sq=package:chromium&type=cs)

Working:
 - Youtube (with https://play.google.com/store/apps/details?id=com.google.android.youtube)

Other apps are not supported because Chromecast now uses V2 of protocol. 

## Authors

The following persons have contributed to leapcast.

 - Janez Troha
 - Tyler Hall
 - Edward Shaw
 - Jan Henrik
 - Martin Polden
 - Thomas Taschauer
 - Zenobius Jiricek
 - Ernes Durakovic
 - Peter Sanford
 - Michel Tu
 - Kaiwen Xu
 - Norman Rasmussen
 - Sven Wischnowsky

## How to install

### Simple

Clone this directory, then run ```python setup.py develop``` or ```pip install leapcast```

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
usage: leapcast [-h] [-d] [-i IPADDRESS] [--name NAME]
                [--user_agent USER_AGENT] [--chrome CHROME] [--fullscreen]
                [--window_size WINDOW_SIZE] [--ips IPS] [--apps APPS]

optional arguments:
  -h, --help            show this help message and exit
  -d, --debug           Debug
  -i IPADDRESS, --interface IPADDRESS
                        Interface to bind to (can be specified multiple times)
  --name NAME           Friendly name for this device
  --user_agent USER_AGENT
                        Custom user agent
  --chrome CHROME       Path to Google Chrome executable
  --fullscreen          Start in full-screen mode
  --window_size WINDOW_SIZE
                        Set the initial chrome window size. eg 1920,1080
  --ips IPS             Allowed ips from which clients can connect
  --apps APPS           Add apps from JSON file

```


[![Bitdeli Badge](https://piwik-ubuntusi.rhcloud.com/piwik.php?idsite=2&amp;rec=1)](https://bitdeli.com/free "Bitdeli Badge")

