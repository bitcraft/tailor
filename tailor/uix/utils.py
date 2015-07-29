import socket
import threading
import logging
import queue

from ..config import pkConfig as pkConfig

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('tailor.utils')


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


class ArduinoHandler:
    def __init__(self):
        self.in_queue = queue.Queue(maxsize=4)
        self.out_queue = queue.Queue(maxsize=100)
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
                    _value = self.in_queue.get(timeout=1)
                except queue.Empty:
                    logger.debug('thread timeout')
                    break
                else:
                    logger.debug('sending %s', str(_value))
                    try:
                        conn.send(str(_value) + '\r\n')
                        self.in_queue.task_done()
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
            self.in_queue.put(value, block=False)
        except queue.Full:
            logger.debug('arduino queue is full')
            try:
                self.in_queue.get()
                self.in_queue.put(value, block=False)
            except (queue.Full, queue.Empty):
                logger.debug('got some error with arduino queue')
                pass

        if self.thread is None:
            logger.debug('starting socket thread')
            self.thread = threading.Thread(target=send_message)
            self.thread.daemon = True
            self.thread.start()
