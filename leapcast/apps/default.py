from __future__ import unicode_literals

from leapcast.services.leap_factory import LEAPfactory


class ChromeCast(LEAPfactory):
    url = "https://www.gstatic.com/cv/receiver.html?{{ query }}"


class YouTube(LEAPfactory):
    url = "https://www.youtube.com/tv?{{ query }}"


class PlayMovies(LEAPfactory):
    url = "https://play.google.com/video/avi/eureka?{{ query }}"
    supported_protocols = ['play-movies', 'ramp']


class GoogleMusic(LEAPfactory):
    url = "https://play.google.com/music/cast/player"


class GoogleCastSampleApp(LEAPfactory):
    url = "http://anzymrcvr.appspot.com/receiver/anzymrcvr.html"


class GoogleCastPlayer(LEAPfactory):
    url = "https://www.gstatic.com/eureka/html/gcp.html"


class Fling(LEAPfactory):
    url = "{{ query }}"

class Pandora_App(LEAPfactory):
    url = "https://tv.pandora.com/cast?{{ query }}"


class TicTacToe(LEAPfactory):
    url = "http://www.gstatic.com/eureka/sample/tictactoe/tictactoe.html"
    supported_protocols = ['com.google.chromecast.demo.tictactoe']
