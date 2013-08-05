# leapcast
![Google Music](http://screencloud.net//img/screenshots/3c17671ad386247d7dbd2f7395c4df77.png "Google Music")

Simple ChromeCast emulation app.

Working:

 - Discovery (DIAL protocol http://www.dial-multiscreen.org/)
 - Youtube
 - Google Music
 - TicTacToe

On real device enabled apps are fetched from https://clients3.google.com/cast/chromecast/device/config


## How to install

### Simple

Clone this directory, then run ```python setup.py develop```

### Better

```
git clone https://github.com/dz0ny/leapcast.git
cd ./leapcast
sudo apt-get install virtualenvwrapper python-pip
mkvirtualenv leapcast
pip install .
```

*** Because updates are frequent I don't recommend normal install. When package is stable enough it will be published to python index and easy installable.
*** For those on windows(tm) gaming platform https://github.com/dz0ny/leapcast/issues/13#issuecomment-21783993

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

```
