from __future__ import unicode_literals

from leapcast.services.leap import LEAP


class ChromeCast(LEAP):
    url = "https://www.gstatic.com/cv/receiver.html?$query"
    protocols = "<protocol>ramp</protocol>"


class YouTube(LEAP):
    url = "https://www.youtube.com/tv?$query"
    protocols = "<protocol>ramp</protocol>"


class PlayMovies(LEAP):
    url = "https://play.google.com/video/avi/eureka?$query"
    protocols = "<protocol>ramp</protocol><protocol>play-movies</protocol>"


class GoogleMusic(LEAP):
    url = "https://jmt17.google.com/sjdev/cast/player"
    protocols = "<protocol>ramp</protocol>"


class GoogleCastSampleApp(LEAP):
    url = "http://anzymrcvr.appspot.com/receiver/anzymrcvr.html"
    protocols = "<protocol>ramp</protocol>"


class GoogleCastPlayer(LEAP):
    url = "https://www.gstatic.com/eureka/html/gcp.html"
    protocols = "<protocol>ramp</protocol>"


class Fling(LEAP):
    url = "$query"
    protocols = "<protocol>ramp</protocol>"


class TicTacToe(LEAP):
    url = "http://www.gstatic.com/eureka/sample/tictactoe/tictactoe.html"
    protocols = "<protocol>com.google.chromecast.demo.tictactoe</protocol>"
