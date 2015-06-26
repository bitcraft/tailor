import logging
import random
import asyncio

from PIL import Image

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('tailor.shuttercamera')


class DummyCamera:
    """
    Debugging interface for a camera.

    Emits auto generated PIL images.
    """
    image_size = 1024, 1024

    def __init__(self):
        self.preview_image = Image.new('RGB', self.image_size, (128, 0, 0))

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

    def download_capture(self):
        """ Capture a full image and return data
        """
        logger.debug('download_capture')
        r = random.randint(0, 255)
        g = random.randint(0, 255)
        b = random.randint(0, 255)
        im = Image.new('RGB', self.image_size, (r, g, b))
        return im

    def download_preview(self):
        """ Capture preview image and return data
        """
        logger.debug('download_preview')
        return self.preview_image
