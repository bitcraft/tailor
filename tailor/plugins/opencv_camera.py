# -*- coding: utf-8 -*-
""" Camera interface using opencv.
"""
import asyncio
import logging
import time

import cv2
from PIL import Image

# Windows dependencies
# - Python 2.7.6: http://www.python.org/download/
# - OpenCV: http://opencv.org/
# - Numpy -- get numpy from here because the official builds don't support x64:
#   http://www.lfd.uci.edu/~gohlke/pythonlibs/#numpy

# Mac Dependencies
# - brew install python
# - pip install numpy
# - brew tap homebrew/science
# - brew install opencv

logger = logging.getLogger('tailor.opencvcamera')


class OpenCVCamera:
    """ Use opencv's camera interface for capturing frames
    """

    def __init__(self, index=0):
        self._device_index = index
        self._device_context = None
        self._lock = asyncio.Lock()

    def __enter__(self):
        self.open()

    def __exit__(self, *args):
        self.close()

    def open(self):
        # TODO: make async
        self._device_context = cv2.VideoCapture(self._device_index)
        time.sleep(2) # give time for camera to init.

        # 'prime' the capture context...
        # some webcams might not init fully until a capture
        # is done.  so we do a capture here to force device to be ready
        self._device_context.read()

    def close(self):
        self._device_context.release()

    def reset(self):
        self.close()
        self.open()

    @staticmethod
    def convert_frame_to_image(frame):
        return Image.fromarray(frame)

    @staticmethod
    async def save_preview():
        """ Capture a preview image and save to a file
        """
        logger.debug('capture_preview, not implemented')

    @staticmethod
    async def save_capture(filename=None):
        """ Capture a full image and save to a file
        """
        # frame = self.capture_frame()
        # cv2.imwrite('capture.jpg', frame)
        # return 'capture.jpg'
        logger.debug('capture_image, not implemented')

    async def capture_frame(self):
        """ Capture a single frame

        :return:
        """
        with (await self._lock):
            ret, frame = self._device_context.read()

        if ret:
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        else:
            rgb = None

        return rgb

    async def capture_image(self):
        """ get frame, decode, and return pil image

        :return:
        """
        frame = await self.capture_frame()
        image = self.convert_frame_to_image(frame)
        return image

    async def download_capture(self):
        """ Capture a full image and return data
        """
        logger.debug('download_capture')
        image = await self.capture_image()
        return image

    async def download_preview(self):
        """ Capture preview image and return data
        """
        image = await self.capture_image()
        return image
