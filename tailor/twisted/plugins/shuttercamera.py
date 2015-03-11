import threading
import logging
from struct import pack

from twisted.plugin import IPlugin
from twisted.internet import defer
from twisted.internet import interfaces
from twisted.internet import threads
from twisted.protocols import basic

from zope.interface import implements
from tailor import itailor
import shutter


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("purikura.shuttercamera")


class PreviewProducer(object):
    implements(interfaces.IPushProducer)

    def __init__(self, proto, camera):
        self._proto = proto
        self._camera = camera
        self._paused = False

    def pauseProducing(self):
        self._paused = True

    @defer.inlineCallbacks
    def resumeProducing(self):
        logger.debug('started to send previews')
        self._paused = False
        try:
            data = yield self._camera.download_preview()
        except shutter.shutter.ShutterError:
            pass
        else:
            self._proto.sendString(data)
        finally:
            self._proto.transport.unregisterProducer()
            self._proto.transport.loseConnection()

    def stopProducing(self):
        pass


class ServePreviews(basic.Int32StringReceiver):
    fmt = '!I'

    def __init__(self, camera):
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


class ShutterCamera(object):
    implements(itailor.ICamera)

    def __init__(self, *args, **kwargs):
        self.capture_filename = 'capture.jpg'
        self.preview_filename = 'preview.jpg'
        self._camera = shutter.Camera(*args, **kwargs)
        self._lock = threading.Lock()

    def create_producer(self):
        return ServePreviews(self)

    def reset(self):
        with self._lock:
            self._camera = None
            self._camera = shutter.Camera()

    def capture_preview(self):
        """ Capture a preview image and save to a file
        """

        def capture():
            with self._lock:
                try:
                    self._camera.capture_preview(self.preview_filename)
                except shutter.shutter.ShutterError:
                    pass
            return self.preview_filename

        return threads.deferToThread(capture)

    def capture_image(self, filename=None):
        """ Capture a full image and save to a file
        """

        def capture():
            with self._lock:
                self._camera.capture_image(self.capture_filename)
            return self.capture_filename

        return threads.deferToThread(capture)

    def download_preview(self):
        """ Capture preview image and return data
        """

        def capture():
            with self._lock:
                return self._camera.capture_preview().get_data()

        return threads.deferToThread(capture)


class ShutterCameraFactory(object):
    implements(IPlugin, itailor.iTailorPlugin)
    __plugin__ = ShutterCamera

    @classmethod
    def new(cls, *args, **kwargs):
        return cls.__plugin__(*args, **kwargs)


factory = ShutterCameraFactory()
