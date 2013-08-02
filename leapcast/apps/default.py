from __future__ import unicode_literals

from leapcast.services.leap import LEAP


class ChromeCast(LEAP):
    url = "https://www.gstatic.com/cv/receiver.html?$query"


class YouTube(LEAP):
    url = "https://www.youtube.com/tv?$query"


class PlayMovies(LEAP):
    url = "https://play.google.com/video/avi/eureka?$query"
    supported_protocols = ['play-movies', 'ramp']


class GoogleMusic(LEAP):
    url = "https://jmt17.google.com/sjdev/cast/player"


class GoogleCastSampleApp(LEAP):
    url = "http://anzymrcvr.appspot.com/receiver/anzymrcvr.html"


class GoogleCastPlayer(LEAP):
    url = "https://www.gstatic.com/eureka/html/gcp.html"


class Fling(LEAP):
    url = "$query"


class TicTacToe(LEAP):
    url = "http://www.gstatic.com/eureka/sample/tictactoe/tictactoe.html"
    supported_protocols = ['com.google.chromecast.demo.tictactoe']
