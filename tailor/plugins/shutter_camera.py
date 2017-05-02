# -*- coding: utf-8 -*-
""" Camera interface for shutter, a libgphoto2 wrapper.
"""
import asyncio
import logging
from io import BytesIO

import shutter
from PIL import Image
import pygame

logger = logging.getLogger("tailor.shutter_camera")

# reduce lookups in to the PIL package namespace
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

    async def capture_preview(self):
        """ Capture preview image (doesn't engage curtain)
        """
        with (await self._lock):
            try:
                raw = self._device_context.capture_preview()
            except shutter.ShutterError:
                return
            return self.convert_raw_to_pil(raw)

    async def capture_image(self, filename=None):
        """ Capture full image (engages full camera mechanisms)
        """
        loop = asyncio.get_event_loop()
        with (await self._lock):
            future = loop.run_in_executor(None,
                                          self._device_context.capture_image)
            await future
        return self.convert_raw_to_pil(future.result())

    async def download_preview(self):
        """ Capture preview image and return data

        :return:
        """
        image = await self.capture_preview()
        return image

    async def download_capture(self):
        """ Capture a full image and return data
        """
        image = await self.capture_image()
        return image
