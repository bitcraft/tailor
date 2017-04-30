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


class TailorStreamingCamera(CameraBase):
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

    def open_socket(self, host, port):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((host, port))
            return s
        except:
            raise

    def once(self, conn):
        max_read = 1024 * 1024

        # TODO: accumulate?
        data = conn.recv(8)
        length = struct.unpack('Q', data)[0]
        to_go = length

        data = bytearray()
        while to_go:
            try:
                get = min(to_go, max_read)
                this_read = conn.recv(get)
                data += this_read
                to_go -= len(this_read)
            except:
                print('data error')
                raise

        # not sure why this occasionally fails?
        # maybe the server end has closed the socket too quickly?
        try:
            packet = cbor.loads(data)
        except:
            print('error')
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

                packet = self.once(conn)

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
