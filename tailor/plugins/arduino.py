import asyncio
import threading
import logging

from zope.interface import implementer
from tailor import itailor

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("tailor.plugins.arduino")


@implementer(itailor.IFileOp)
class Arduino:
    pass


# basic.LineReceiver
class ArduinoProtocol(asyncio.StreamReader):
    """
    protocol:

    0x01: trigger
    0x80: set servo
    0x81: engage relay
    0x82: disengage relay
    """

    def __init__(self, session):
        logger.debug('new arduino')
        self.session = session
        self.lock = threading.Lock()

    def process(self, cmd, arg):
        logger.debug('processing for arduino: %s %s', cmd, arg)
        if cmd == 1 and arg == 2:
            self.session.start(arduino=self)

    def sendCommand(self, cmd, arg):
        logger.debug('sending to arduino: %s %s', cmd, arg)
        data = chr(cmd) + chr(arg)
        self.transport.write(data)

    def lineReceived(self, data):
        logger.debug('got serial data %s', data)
        try:
            cmd, arg = [int(i) for i in data.split()]
            logger.debug('got command %s %s', cmd, arg)
            self.process(cmd, arg)
        except ValueError:
            logger.debug('unable to parse: %s', data)
            raise


# basic.LineReceiver
class ServoServiceProtocol(protocols.Protocol):
    def lineReceived(self, data):
        logger.debug('got remote data %s', data)
        value = None

        try:
            value = int(data)
        except ValueError:
            logger.debug('cannot process data %s', data)

        if value == -1:
            self.transport.loseConnection()
            return

        else:
            try:
                self.factory.arduino.sendCommand(0x80, value)
            except:
                logger.debug('problem communicating with arduino')
                raise


# protocol.ServerFactory
class ServoServiceFactory(asyncio.Protocol):
    protocol = ServoServiceProtocol

    def __init__(self, arduino):
        self._arduino = arduino

    @property
    def arduino(self):
        return self._arduino
