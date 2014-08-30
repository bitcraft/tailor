#!/bin/sh
export SDL_VIDEO_FULLSCREEN_DISPLAY=0.0

amixer -c 0 set PCM 100%
amixer -c 0 set Master 100%

while true
do
    python service.py &
    sleep 5
    python kiosk.py &&
    OUT=$?
    killall -9 python
    if [ "$OUT" -eq "0" ]; then
        sleep 1
    else
        break
    fi
done
killall -9 python
exit $OUT
