import shutter
import time


def reset():
    c = shutter.Camera()
    c.capture_image()


while 1:
    reset()
    time.sleep(2)
