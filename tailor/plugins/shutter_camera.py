# -*- coding: utf-8 -*-
""" Camera interface for shutter, a libgphoto2 wrapper.
"""
import asyncio
import logging
import platform

import shutter

logger = logging.getLogger("tailor.shutter_camera")


def release_from_tight_grip_of_operating_system():
    if platform.system() == 'Linux':
        from tailor.core.unix import release_gvfs_from_camera

        try:
            release_gvfs_from_camera()
        except FileNotFoundError:
            pass


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
        self.open_camera()

    def open_camera(self):
        release_from_tight_grip_of_operating_system()
        self._device_context = shutter.Camera(self._device_name_regex)

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

    async def capture_preview(self):
        """ Capture preview image (doesn't engage curtain)
        """
        with (await self._lock):
            try:
                return self._device_context.capture_preview()
            except shutter.ShutterError:
                logger.critical("cannot capture preview, attempting to get camera")
                release_from_tight_grip_of_operating_system()
                await(asyncio.sleep(1))
                self.open_camera()

    async def capture_image(self, filename=None):
        """ Capture full image (engages full camera mechanisms)
        """
        executor = asyncio.get_event_loop().run_in_executor
        with (await self._lock):
            future = executor(None, self._device_context.capture_image)
            await future
        return future.result()

    async def download_preview(self):
        """ Capture preview image and return data

        :return:
        """
        return await self.capture_preview()

    async def download_capture(self):
        """ Capture a full image and return data
        """
        return await self.capture_image()
