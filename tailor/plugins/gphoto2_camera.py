# -*- coding: utf-8 -*-
""" Camera interface for the python-gphoto2 wrapper.
"""
import platform
import asyncio
import logging

import gphoto2 as gp

logger = logging.getLogger("tailor.gphoto2_camera")


def release_from_tight_grip_of_operating_system():
    if platform.system() == 'Linux':
        from tailor.core.unix import release_gvfs_from_camera

        try:
            release_gvfs_from_camera()
        except FileNotFoundError:
            pass


class GphotoCamera:
    """ Shutter is a wrapper for glibphoto2 to capture frames from dSLR cameras
    """

    def __init__(self, regex=None):
        self._context = None
        self._camera = None
        self._lock = asyncio.Lock()
        self._device_name_regex = regex

    def __enter__(self):
        self.open()

    def __exit__(self, *args):
        self.close()

    def open(self):
        self.open_camera()

    def open_camera(self):
        # the following needs to be changed into some
        # kind of context manager aware delay to allow
        # the camera to get ready in a context manager
        release_from_tight_grip_of_operating_system()

        ctx = gp.gp_context_new()
        error, camera = gp.gp_camera_new()
        gp.check_result(gp.gp_camera_init(camera, ctx))

        # TODO: check if camera cannot be used for some reason

        self._camera = camera
        self._context = ctx

    def close(self):
        self.close_camera()

    def close_camera(self):
        # the following isn't going to work with async yet
        # self.close()
        gp.check_result(gp.gp_camera_exit(self._camera, self._context))
        self._camera = None
        self._context = None

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
            file = gp.check_result(gp.gp_camera_capture_preview(self._camera, self._context))
            data = gp.check_result(gp.gp_file_get_data_and_size(file))
            return bytes(data)

    async def capture_image(self, filename=None):
        """ Capture full image (engages full camera mechanisms)
        
        filename not supported
        """

        def capture():
            path = gp.check_result(gp.gp_camera_capture(self._camera, gp.GP_CAPTURE_IMAGE, self._context))

            file = gp.check_result(gp.gp_camera_file_get(
                self._camera, path.folder, path.name,
                gp.GP_FILE_TYPE_NORMAL, self._context))

            data = gp.check_result(gp.gp_file_get_data_and_size(file))
            return bytes(data)

        executor = asyncio.get_event_loop().run_in_executor

        with (await self._lock):
            future = executor(None, capture)
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
