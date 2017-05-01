# -*- coding: utf-8 -*-
import queue
import socket
import threading
import struct

import cbor
from kivy.clock import Clock
from kivy.core.camera import CameraBase
from kivy.core.image import ImageData
from kivy.graphics.texture import Texture

from uix.utils import logger


def recv(sock, length, max_read=4096):
    """ read data from port for exactly length bytes
    """
    data = bytearray()
    while length:
        get = min(length, max_read)
        this_read = sock.recv(get)
        data += this_read
        length -= len(this_read)

    return data


class TailorStreamingCamera(CameraBase):
    """ Currently not used!
        Conceptually, this is just a simple widget for streaming uncompressed video frames
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.queue = queue.Queue()
        self._format = 'rgb'

    def init_camera(self):
        if not self.stopped:
            self.start()

    def start(self):
        super().start()
        Clock.unschedule(self._update)
        Clock.schedule_interval(self._update, self.fps)

    def stop(self):
        super().stop()
        Clock.unschedule(self._update)

    def _update(self, dt):
        if self.stopped:
            return

        if self._texture is None:
            # Create the texture
            self._texture = Texture.create(self._resolution)
            self._texture.flip_vertical()
            self.dispatch('on_load')
        try:
            self._buffer = self._grab_last_frame()
            self._copy_to_gpu()
        except:
            # Logger.exception('OpenCV: Couldn\'t get image from Camera')
            pass

    def _grab_last_frame(self):
        try:
            image_data = self.queue.get(False)
        except queue.Empty:
            return

        return image_data


class PreviewHandler:
    # TODO: allow thread to signal to parent that it cannot get data
    def __init__(self):
        self.queue = queue.Queue(maxsize=2)
        self.thread = None
        self.running = False

    @staticmethod
    def open_socket(host, port):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((host, port))
            return s
        except:
            raise

    @staticmethod
    def get_packet(conn):
        max_read = 262144 # value is just guesswork

        data = recv(conn, 8, max_read)
        length = struct.unpack('Q', data)[0]
        data = recv(conn, length, max_read)

        # not sure why this occasionally fails?
        # maybe the server end has closed the socket too quickly?
        try:
            packet = cbor.loads(data)
        except:
            print('preview packet decode error')
            return

        return packet

    def start(self):
        def func():
            self.running = True
            queue_put = self.queue.put

            host = 'localhost'
            port = 22222
            conn = None

            while self.running:
                if conn is None:
                    conn = self.open_socket(host, port)

                packet = self.get_packet(conn)

                if packet:
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

                else:
                    print('could not decode packet, giving up')
                    conn.close()
                    conn = None

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
