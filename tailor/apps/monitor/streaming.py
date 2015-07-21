import queue
import logging
import socket
import threading
from io import StringIO
from PIL import Image as PIL_Image
from kivy.core.image import ImageData

logger = logging.getLogger('tailor.apps.monitor.streaming')


class PreviewHandler:
    """
    The socket handling needs to be reworked.

    Currently is just hammers the host and rapidly opens and closes a socket.
    should instead open socket, stream data and close after a timeout (30 seconds?).
    """
    def __init__(self):
        self.queue = queue.Queue(maxsize=10)
        self.thread = None
        self.running = False

    def start(self):
        def func():
            self.running = True
            queue_put = self.queue.put
            pil_open = PIL_Image.open

            host = 'localhost'
            port = 23453
            buffer_size = 1024

            while self.running:
                try:
                    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    s.connect((host, port))
                except:
                    raise

                data = ''
                try:
                    chunk = s.recv(buffer_size)
                    while len(chunk):
                        data += chunk
                        chunk = s.recv(buffer_size)
                    s.close()
                    data = data[4:]
                except:
                    raise

                try:
                    image = pil_open(StringIO(str(data)))
                except IOError:
                    continue

                image = self.flip_image(image)
                image_data = self.create_kivy_image_data(image)

                # this will block until the consumer has taken an image
                # it's a good thing (tm)
                queue_put(image_data)

        if self.thread is None:
            logger.debug('starting the preview handler')
            self.thread = threading.Thread(target=func)
            self.thread.daemon = True
            self.thread.start()

    def stop(self):
        if self.thread is None:
            logger.debug('want to stop preview thread, but is not running')
        else:
            logger.debug('stopping the preview handler')
            self.running = False

    @staticmethod
    def fit_image(image):
        w, h = image.size
        ww = 1.55 * 300
        hh = 1.27 * 300
        scale = hh / h
        sw = int(w * scale)
        cx = int((sw - ww) / 2)
        image = image.resize((int(sw), int(hh)), PIL_Image.ANTIALIAS)
        image = image.crop((int(cx), 0, int(sw - cx), int(hh)))
        image.load()
        return image

    @staticmethod
    def flip_image(image):
        return image.transpose(PIL_Image.FLIP_TOP_BOTTOM)

    @staticmethod
    def create_kivy_image_data(image):
        return ImageData(image.size[0], image.size[1], image.mode.lower(), image.tostring())

