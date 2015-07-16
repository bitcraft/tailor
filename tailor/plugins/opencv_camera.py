import time
import logging

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

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('tailor.opencvcamera')


class OpenCVCamera:
    """
    Debugging interface for a camera.

    Emits auto generated PIL images.
    """
    def __init__(self):
        self.device_context = None

    def __enter__(self):
        self.open()

    def __exit__(self, *args):
        self.close()

    def open(self):
        dc = cv2.VideoCapture(0)

        # give time for webcam to init.
        time.sleep(2)

        # 'prime' the capture context...
        # some webcams might not init fully until a capture
        # is done.  so we do a capture here to force device to be ready
        dc.read()

        self.device_context = dc

    def close(self):
        self.device_context.release()

    def reset(self):
        self.close()
        self.open()

    def capture_frame(self):
        """ Capture a single frame

        :return:
        """
        ret, frame = self.device_context.read()
        if ret:
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGBA)
        else:
            rgb = None

        return rgb

    @staticmethod
    def convert_frame_to_image(frame):
        return Image.fromarray(frame)

    def capture_image(self):
        """ get frame, decode, and return pil image

        :return:
        """
        frame = self.capture_frame()
        image = self.convert_frame_to_image(frame)
        return image

    def save_preview(self):
        """ Capture a preview image and save to a file
        """
        logger.debug('capture_preview, not implemented')

    def save_capture(self, filename=None):
        """ Capture a full image and save to a file
        """
        # frame = self.capture_frame()
        # cv2.imwrite('capture.jpg', frame)
        # return 'capture.jpg'
        logger.debug('capture_image, not implemented')

    def download_capture(self):
        """ Capture a full image and return data
        """
        logger.debug('download_capture')
        image = self.capture_image()
        return image

    def download_preview(self):
        """ Capture preview image and return data
        """
        logger.debug('download_preview')
        return self.capture_image()
