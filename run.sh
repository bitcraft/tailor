#!/bin/sh
export SDL_VIDEO_FULLSCREEN_DISPLAY=0.0

amixer -c 0 set PCM 100%
amixer -c 0 set Master 100%

python service.py &
sleep 5
python kiosk.py &&
killall -9 python
exit $OUT
