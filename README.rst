leapcast
========

|Flattr this git repo| |Build Status| |Stats|

Simple ChromeCast emulation app.

Working:

-  Discovery (DIAL protocol http://www.dial-multiscreen.org/)
-  Youtube (with
   https://play.google.com/store/apps/details?id=com.google.android.youtube)
-  Google Music (with
   https://play.google.com/store/apps/details?id=com.google.android.music)
-  HBO GO (with https://play.google.com/store/apps/details?id=com.HBO)
-  Hulu Plus (with
   https://play.google.com/store/apps/details?id=com.hulu.plus)
-  Pandora (with
   https://play.google.com/store/apps/details?id=com.pandora.android )
-  RedBull TV (with
   https://play.google.com/store/apps/details?id=com.nousguide.android.rbtv)
-  Others (see
   http://en.wikipedia.org/wiki/Chromecast#Chrome\_and\_mobile\_apps)

On real device enabled apps are fetched from
https://clients3.google.com/cast/chromecast/device/config . Bugs in
ChromeCast SDK are listed at
https://code.google.com/p/google-cast-sdk/issues/list?can=2&q=&sort=priority&colspec=ID%20Type%20Status%20Priority%20Milestone%20Owner%20Summary

Some known bugs in ChromeCast SDK:

-  Discovery fails on some devices with multiple unactive network
   interfaces
-  Scanning crashes device or app with ConcurrentModificationException

Authors
-------

The following persons have contributed to leapcast.

-  Janez Troha
-  Tyler Hall
-  Edward Shaw
-  Jan Henrik
-  Martin Polden
-  Thomas Taschauer
-  Zenobius Jiricek
-  Ernes Durakovic
-  Peter Sanford
-  Michel Tu
-  Kaiwen Xu
-  Norman Rasmussen
-  Sven Wischnowsky

How to install
--------------

Simple
~~~~~~

Clone this directory, then run ``python setup.py develop`` or
``pip install leapcast``

Better
~~~~~~

::

    git clone https://github.com/dz0ny/leapcast.git
    cd ./leapcast
    sudo apt-get install virtualenvwrapper python-pip python-twisted-web python2.7-dev
    mkvirtualenv leapcast
    pip install .

Windows
^^^^^^^

For those on Windows(tm) follow this guide
https://gist.github.com/eyecatchup/6219118 or
https://plus.google.com/100317092290545434762/posts/8RjWfMXxje8

::

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

|Bitdeli Badge|

.. |Flattr this git repo| image:: http://api.flattr.com/button/flattr-badge-large.png
   :target: https://flattr.com/submit/auto?user_id=dz0ny&url=https://github.com/dz0ny/leapcast&title=Leapcast&language=&tags=github&category=software
.. |Build Status| image:: https://travis-ci.org/dz0ny/leapcast.png?branch=master
   :target: https://travis-ci.org/dz0ny/leapcast
.. |Stats| image:: https://ga-beacon.appspot.com/UA-46813385-1/dz0ny/leapcast
   :target: https://github.com/dz0ny/leapcast
.. |Bitdeli Badge| image:: https://piwik-ubuntusi.rhcloud.com/piwik.php?idsite=2&rec=1
   :target: https://bitdeli.com/free
