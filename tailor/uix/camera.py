# -*- coding: utf-8 -*-
import logging
import queue
import socket
import struct
import threading

import cbor
from kivy.clock import Clock
from kivy.core.camera import CameraBase
from kivy.graphics.texture import Texture

logger = logging.getLogger("tailor.camera")


def recv(sock, length, max_read=4096):
    """ read data from port for exactly length bytes
    """
    # TODO: generator interface to allow byte consumption past packet boundary
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
        self._format = "rgb"

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
            self._texture = Texture.create(self._resolution)
            self._texture.flip_vertical()
            self.dispatch("on_load")
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
        self.queue = queue.Queue(maxsize=1)
        self.thread = None
        self.running = False
        self.host = "localhost"
        self.port = 22222

        # maximum amount of bytes to request each socket read
        # value is just guesswork
        self.max_read = 262144

    @staticmethod
    def open_socket(host, port):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((host, port))
            return sock
        except:
            raise

    def get_packet(self, sock):
        """ Get one frame from a socket

        :param sock:
        :rtype: dict
        """
        # get the "header", just a 64-bit integer
        data = recv(sock, 8, self.max_read)
        length = struct.unpack("Q", data)[0]

        # get the rest of the data
        data = recv(sock, length, self.max_read)

        try:
            packet = cbor.loads(data)
            # TODO: check for more exceptions, IDK
        except (ValueError, EOFError):
            logger.debug("preview packet decode error")
            return

        return packet

    def start(self):
        def func():
            self.running = True
            queue_put = self.queue.put
            sock = None

            while self.running:
                if sock is None:
                    sock = self.open_socket(self.host, self.port)

                # the 1 byte signals that the a preview is needed
                sock.send(b"\x01")

                packet = self.get_packet(sock)

                if packet:
                    queue_put(packet)

                else:
                    logger.debug("could not decode packet, giving up")
                    sock.send(b"\xFF")
                    sock.close()
                    sock = None

            if sock:
                logger.debug("stopping preview thread gracefully")
                sock.send(b"\xFF")
                sock.close()

        if self.thread is None:
            logger.debug("starting the preview handler")
            self.thread = threading.Thread(target=func)
            self.thread.daemon = True
            self.thread.start()

    def stop(self):
        if self.thread is None:
            logger.debug("want to stop preview thread, but is not running")
        else:
            logger.debug("stopping the preview handler")
            self.running = False
