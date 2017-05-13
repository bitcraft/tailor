# -*- coding: utf-8 -*-
""" Camera interface for debugging.  Generates random colored images.

"""
import io
import logging
import random

from PIL import Image

logger = logging.getLogger('tailor.shuttercamera')


class DummyCamera:
    """
    Debugging interface for a camera.

    Emits auto generated PIL images.
    """
    image_size = 1024, 1024

    def __enter__(self):
        self.open()
        self.preview_image = None

    def __exit__(self, *args):
        self.close()

    def open(self):
        """ Initialize device or driver

        :return:
        """
        # fp = io.BytesIO()
        # im = Image.new('RGB', self.image_size, (128, 0, 0))
        # im.save(fp, format='JPEG')
        # self.preview_image = fp.getvalue()
        pass

    def close(self):
        """ Uninitialize device or driver

        :return:
        """
        del self.preview_image

    def reset(self):
        pass

    def save_preview(self):
        """ Capture a preview image and save to a file
        """
        logger.debug('capture_preview, not implemented')

    def save_capture(self, filename=None):
        """ Capture a full image and save to a file
        """
        logger.debug('capture_image, not implemented')

    async def download_capture(self):
        """ Capture a full image and return data
        """
        logger.debug('download_capture')
        r = random.randint(0, 255)
        g = random.randint(0, 255)
        b = random.randint(0, 255)
        fp = io.BytesIO()
        im = Image.new('RGB', self.image_size, (r, g, b))
        im.save(fp, "JPEG")
        return fp.getvalue()

    async def download_preview(self):
        """ Capture preview image and return data
        """
        logger.debug('download_preview')
        fp = io.BytesIO()
        im = Image.new('RGB', self.image_size, (128, 0, 0))
        im.save(fp, format='JPEG')
        return  fp.getvalue()
