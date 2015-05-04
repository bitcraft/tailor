import logging

from zope.interface import implementer
from zope.interface import implementer

from tailor import itailor


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('tailor.shuttercamera')


@implementer(itailor.ICamera)
class DummyCamera:
    def __init__(self, *args, **kwargs):
        self.capture_filename = 'capture.jpg'
        self.preview_filename = 'preview.jpg'

    def reset(self):
        pass

    def save_preview(self):
        ''' Capture a preview image and save to a file
        '''
        logger.debug('capture_preview')

    def save_capture(self, filename=None):
        ''' Capture a full image and save to a file
        '''
        logger.debug('capture_image')

    def download_capture(self):
        ''' Capture a full image and return data
        '''
        logger.debug('download_capture')

    def download_preview(self):
        ''' Capture preview image and return data
        '''
        logger.debug('download_preview')
