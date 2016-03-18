# -*- coding: utf-8 -*-
"""
needs asyncio audit
"""
import asyncio
import logging
import time

from PIL import Image

# Windows dependencies
# - Python 2.7.6: http://www.python.org/download/
#   http://www.lfd.uci.edu/~gohlke/pythonlibs/#pygame

logger = logging.getLogger('tailor.pygame_camera')
from pygame.image import tostring


class PygameCamera:
    """ Use pygame's webcam module for capturing frames
    """

    # pygame doesn't expose a way to query for available resolutions
    # the included default is just a common value.  if the webcam
    # doesn't support this value, it will default to the highest
    # available that is lower than the default.  This class will handle
    # this, and will adjust accordingly.
    default_resolution = 1920, 1080

    def __init__(self, index=0):
        self._device_index = index
        self._device_context = None
        self._frame_size = None
        self._lock = asyncio.Lock()
        self._temp_surface = None

    def __enter__(self):
        self.open()

    def __exit__(self, *args):
        self.close()

    def open(self):
        # TODO: make async
        from pygame import camera

        camera.init()
        cameras = camera.list_cameras()
        dc = camera.Camera(cameras[self._device_index], self.default_resolution, 'RGB')
        dc.start()

        time.sleep(1)  # give time for webcam to init.

        # 'prime' the capture context...
        # some webcams might not init fully until a capture
        # is done.  so we do a capture here to force device to be ready
        # and query the maximum supported size
        self._temp_surface = dc.get_image()
        self._device_context = dc

    def close(self):
        self._device_context.close()

    def reset(self):
        self.close()
        self.open()

    @asyncio.coroutine
    def capture_frame(self):
        """ Capture a single frame

        :return:
        """
        with (yield from self._lock):
            self._device_context.get_image(self._temp_surface)

    def convert_frame_to_image(self, frame):
        return Image.frombytes('RGB', self._temp_surface.get_size(),
                               tostring(self._temp_surface, 'RGB'))

    @asyncio.coroutine
    def capture_image(self):
        """ get frame, decode, and return pil image

        :return:
        """
        frame = yield from self.capture_frame()
        image = self.convert_frame_to_image(frame)
        return image

    @asyncio.coroutine
    def save_preview(self):
        """ Capture a preview image and save to a file
        """
        logger.debug('capture_preview, not implemented')

    @asyncio.coroutine
    def save_capture(self, filename=None):
        """ Capture a full image and save to a file
        """
        # frame = self.capture_frame()
        # cv2.imwrite('capture.jpg', frame)
        # return 'capture.jpg'
        logger.debug('capture_image, not implemented')

    @asyncio.coroutine
    def download_capture(self):
        """ Capture a full image and return data
        """
        logger.debug('download_capture')
        image = yield from self.capture_image()
        return image

    @asyncio.coroutine
    def download_preview(self):
        """ Capture preview image and return data
        """
        image = yield from self.capture_image()
        return image
