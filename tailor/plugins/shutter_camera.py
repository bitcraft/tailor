# -*- coding: utf-8 -*-
import asyncio
import logging
from io import BytesIO

import shutter
from PIL import Image

logger = logging.getLogger("tailor.shutter_camera")

# reduce lookups in to the PIL package
pil_open = Image.open


class ShutterCamera:
    """ Shutter is a wrapper for glibphoto2 to capture frames from dSLR cameras
    """

    def __init__(self, regex=None):
        self._device_context = None
        self._lock = asyncio.Lock()
        self._device_name_regex = regex

    def __enter__(self):
        # the following isn't going to work with async yet
        # self.open()

        # the following needs to be changed into some
        # kind of context manager aware delay to allow
        # the camera to get ready in a context manager
        self._device_context = shutter.Camera(self._device_name_regex)
        import time
        time.sleep(1)

    def __exit__(self, *args):
        # the following isn't going to work with async yet
        # self.close()
        self._device_context = None

    # @asyncio.coroutine
    # def open(self):
    #     with (yield from self._lock):
    #         self._device_context = shutter.Camera()
    #
    # @asyncio.coroutine
    # def close(self):
    #     # TODO: verify this closes the libgphoto obj
    #     with (yield from self._lock):
    #         self._device_context = None
    #
    # @asyncio.coroutine
    # def reset(self):
    #     yield from self.close()
    #     yield from self.open()

    @staticmethod
    def convert_raw_to_pil(raw):
        return pil_open(BytesIO(raw))

    @asyncio.coroutine
    def capture_preview(self):
        """ Capture preview image (doesn't engage curtain)
        """
        with (yield from self._lock):
            try:
                image = self._device_context.capture_preview()
                return self.convert_raw_to_pil(image)
            except shutter.ShutterError:
                # errors are ignored since preview images are not important
                return

    @asyncio.coroutine
    def capture_image(self, filename=None):
        """ Capture full image (engages full camera mechanisms)
        """
        loop = asyncio.get_event_loop()
        with (yield from self._lock):
            future = loop.run_in_executor(None,
                                          self._device_context.capture_image)
            yield from future
        return self.convert_raw_to_pil(future.result())

    @asyncio.coroutine
    def download_preview(self):
        """ Capture preview image and return data

        :return:
        """
        image = yield from self.capture_preview()
        return image

    @asyncio.coroutine
    def download_capture(self):
        """ Capture a full image and return data
        """
        image = yield from self.capture_image()
        return image
