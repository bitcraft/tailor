import logging
from struct import pack

import shutter

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("purikura.shuttercamera")


class PreviewProducer:
    def __init__(self, proto, camera):
        self._proto = proto
        self._camera = camera
        self._paused = False

    def pauseProducing(self):
        self._paused = True

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
        logger.debug('lost connection')
        pass

    def sendString(self, data):
        self.transport.write(pack(self.fmt, len(data)) + data)
