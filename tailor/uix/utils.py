# -*- coding: utf-8 -*-
import socket
import threading
import logging
import queue
import pickle

from kivy.core.image import ImageData

logger = logging.getLogger('tailor.utils')


def trigger_session_via_socket():
    # currently the trigger to start the session is to
    # open a socket then close it.  perfect, no.  works, yes?
    import socket
    host, port = '127.0.0.1', 22223
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((host, port))
        s.close()
    except:
        pass


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


class PreviewHandler:
    # TODO: allow thread to signal to parent that it cannot get data
    def __init__(self):
        self.queue = queue.Queue(maxsize=10)
        self.thread = None
        self.running = False

    def start(self):
        def func():
            self.running = True
            queue_put = self.queue.put

            host = 'localhost'
            port = 22222
            buffer_size = 1024

            while self.running:
                try:
                    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    s.connect((host, port))
                except:
                    raise

                data = bytearray()
                try:
                    chunk = s.recv(buffer_size)
                    while len(chunk):
                        data += chunk
                        chunk = s.recv(buffer_size)
                    s.close()
                except:
                    continue

                try:
                    packet = pickle.loads(data)
                except:
                    continue

                image_data = packet['image_data']
                session = packet['session']

                size = image_data['size']
                imdata = ImageData(size[0],
                                   size[1],
                                   image_data['mode'].lower(),
                                   image_data['data'])

                # this will block until the consumer has taken an image
                # it's a good thing (tm)
                queue_put((session, imdata))

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
