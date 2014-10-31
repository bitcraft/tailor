from kivy.core.image import ImageData
from PIL import Image as PIL_Image
from six.moves import queue
from six.moves import cStringIO

import socket
import threading
import logging

from ..config import Config as pkConfig

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('purikura.utils')


# hack search method because one is not included with kivy
def search(root, uniqueid):
    children = root.children[:]
    while children:
        child = children.pop()
        children.extend(child.children[:])

        try:
            child.uniqueid
        except:
            continue
        else:
            if child.uniqueid == uniqueid:
                return child

    return None


class PreviewHandler(object):
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
                    im = pil_open(cStringIO(str(data)))
                except IOError:
                    continue

                # HACK
                w, h = im.size
                ww = 1.55 * 300
                hh = 1.27 * 300
                scale = hh / h
                sw = int(w * scale)
                cx = int((sw - ww) / 2)
                im = im.resize((int(sw), int(hh)), PIL_Image.ANTIALIAS)
                im = im.crop((int(cx), 0, int(sw - cx), int(hh)))
                im.load()

                im = im.transpose(PIL_Image.FLIP_TOP_BOTTOM)
                imdata = ImageData(im.size[0],
                                   im.size[1],
                                   im.mode.lower(),
                                   im.tostring())

                # this will block until the consumer has taken an image
                # it's a good thing (tm)
                queue_put(imdata)

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


class ArduinoHandler(object):
    def __init__(self):
        self.queue = queue.Queue(maxsize=4)
        self.lock = threading.Lock()
        self.thread = None

    def set_camera_tilt(self, value):
        """ Set camera tilt

        TODO: some kind of smoothing.
        """

        def send_message():
            host = 'localhost'
            port = pkConfig.getint('arduino', 'tcp-port')

            try:
                conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                conn.connect((host, port))
            except:
                self.thread = None
                return

            while 1:
                try:
                    logger.debug('waiting for value...')
                    _value = self.queue.get(timeout=1)
                except queue.Empty:
                    logger.debug('thread timeout')
                    break
                else:
                    logger.debug('sending %s', str(_value))
                    try:
                        conn.send(str(_value) + '\r\n')
                        self.queue.task_done()
                    except:
                        break

            logger.debug('closing connection')
            try:
                conn.send(str(-1) + '\r\n')
                conn.close()
            except:
                pass

            logger.debug('end of thread')
            self.thread = None
            return

        try:
            logger.debug('adding value to arduino queue')
            self.queue.put(value, block=False)
        except queue.Full:
            logger.debug('arduino queue is full')
            try:
                self.queue.get()
                self.queue.put(value, block=False)
            except (queue.Full, queue.Empty):
                logger.debug('got some error with arduino queue')
                pass

        if self.thread is None:
            logger.debug('starting socket thread')
            self.thread = threading.Thread(target=send_message)
            self.thread.daemon = True
            self.thread.start()
