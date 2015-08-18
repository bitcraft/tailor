import asyncio
import threading
from struct import pack
import logging

import shutter

logger = logging.getLogger("tailor.shuttercamera")


class PreviewProducer:
    def __init__(self, proto, camera):
        self._proto = proto
        self._camera = camera

    def resumeProducing(self):
        logger.debug('started to send previews')
        try:
            data = yield self._camera.download_preview()
        except shutter.ShutterError:
            pass
        else:
            self._proto.sendString(data)
        finally:
            self._proto.transport.unregisterProducer()
            self._proto.transport.loseConnection()


class ServePreviews(asyncio.StreamWriter):
    fmt = '!I'

    def __init__(self, camera):
        super().__init__()
        self._camera = camera

    def connectionMade(self):
        p = PreviewProducer(self, self._camera)
        self.transport.registerProducer(p, True)
        p.resumeProducing()

    def connectionLost(self, reason):
        # logger.debug('lost connection')
        pass

    def sendString(self, data):
        self.transport.write(pack(self.fmt, len(data)) + data)


class ShutterCamera:
    def __init__(self, *args, **kwargs):
        self.capture_filename = 'capture.jpg'
        self.preview_filename = 'preview.jpg'
        self._camera = shutter.Camera(*args, **kwargs)
        self._lock = threading.Lock()

    def create_streaming_preview_server(self):
        loop = asyncio.get_event_loop()
        server = loop.create_server(factory)

    def reset(self):
        with self._lock:
            self._camera = None
            self._camera = shutter.Camera()

    def capture_preview(self):
        """ Capture a preview image and save to a file
        """
        with self._lock:
            try:
                self._camera.capture_preview(self.preview_filename)
            except shutter.ShutterError:
                # errors are ignored since preview images are not important
                pass
        return self.preview_filename

    def capture_image(self, filename=None):
        """ Capture a full image and save to a file
        """
        with self._lock:
            self._camera.capture_image(self.capture_filename)
        return self.capture_filename

    def download_capture(self):
        """ Capture a full image and return data
        """
        with self._lock:
            return self._camera.capture_image().get_data()

    def download_preview(self):
        """ Capture preview image and return data
        """
        with self._lock:
            return self._camera.capture_preview().get_data()
