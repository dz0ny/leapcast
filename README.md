leapcast
========

Simple ChromeCast emulation app.

Working:

 - Discovery (DIAL protocol http://www.dial-multiscreen.org/)
 - Default apps

Apps:

 - YouTube uses REST CloudProxy or local Websocket
 - Google music uses STOMP CloudProxy 
 - ChromeCast local websocket and stomp, video is streamed to port 8090
 - Fling local websocket and stomp, launches any url

On real device enabled apps are fetched from https://clients3.google.com/cast/chromecast/device/config

TODO:

 - Play mode
 - Remote control via STOMP and Websockets
