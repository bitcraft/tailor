#!/usr/bin/env python
"""
This program is the nuts and bolts of the photo booth.
"""
import sys
import os

# make service work without installing tailor into python
app_root_path = os.path.realpath(os.path.join(__file__, '..', '..', '..'))
sys.path.append(app_root_path)
sys.path.append(os.path.join(app_root_path, 'tailor'))

from twisted.internet import reactor, defer, task, protocol
from twisted.internet.serialport import SerialPort
from twisted.protocols import basic
from twisted.plugin import getPlugins
from six.moves import configparser
import serial
import traceback
import threading
import pygame
pygame.mixer.init()

import re

from tailor import itailor
from tailor import resources
from tailor import template
from tailor.config import Config

import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("purikura.booth")

# because i hate typing
jpath = os.path.join

# paths
app_resources_path = jpath(app_root_path, 'resources')
app_sounds_path = jpath(app_resources_path, 'sounds')
app_images_path = jpath(app_resources_path, 'images')
all_templates_path = jpath(app_resources_path, 'templates')
all_images_path = Config.get('paths', 'images')
shared_path = Config.get('paths', 'shared')

# event paths
event_name = Config.get('event', 'name')
template_path = jpath(all_templates_path, Config.get('event', 'template'))
event_images_path = jpath(all_images_path, event_name)
thumbs_path = jpath(event_images_path, 'thumbnails')
details_path = jpath(event_images_path, 'detail')
originals_path = jpath(event_images_path, 'originals')
composites_path = jpath(event_images_path, 'composites')
paths = ('thumbnails', 'detail', 'originals', 'composites')

# make sure directory structure is usuable
if Config.getboolean('paths', 'make-images-path'):
    for d in (thumbs_path, details_path, originals_path, composites_path):
        try:
            isdir = os.path.isdir(d)
        except:
            raise
        if not isdir:
            os.makedirs(d, 0755)

# mixer must be initialized before sounds will play
#pygame.mixer.init(frequency=Config.getint('sound', 'mixer-frequency'),
#                  buffer=Config.getint('sound', 'mixer-buffer'))

# load all the stuff
resources.load(app_resources_path)

# i'm lazy!
bell0 = resources.sounds['bell0']
bell1 = resources.sounds['bell1']
error = resources.sounds['error']
finished = resources.sounds['finished']

# manage volumes a bit
bell1.set_volume(bell1.get_volume() * 1.0)
finished.set_volume(finished.get_volume() * .6)

in_session = False
arduino = None

def get_class(o):
    name = o.__class__.__name__
    if name.endswith('Factory'):
        return name[:-7]
    else:
        return name


class Session:
    def __init__(self):
        logger.debug('building new session...')

        self.template = configparser.ConfigParser()
        self.template.read(template_path)
        self.camera = None

        self.plugins = dict((get_class(p), p) for p in
                            getPlugins(itailor.iTailorPlugin))

        for name in self.plugins.keys():
            logger.debug("loaded plugin %s", name)

        self.camera = self.plugins['ShutterCamera'].new(
            re.compile(Config.get('camera', 'name')))

    def capture(self):
        def shutter(result=None):
            if arduino:
                arduino.sendCommand(0x82, 0)
                arduino.sendCommand(0x82, 1)
            d = self.camera.capture_image()
            return d

        interval = Config.getint('camera', 'countdown-interval')
        c = task.LoopingCall(bell0.play)
        d = c.start(interval)
        d = d.addCallback(shutter)
        task.deferLater(reactor, 3 * interval, c.stop)
        if arduino:
            arduino.sendCommand(0x81, 0)
            arduino.sendCommand(0x81, 1)
        return d

    @defer.inlineCallbacks
    def start(self, result=None, arduino=None):
        global in_session

        logger.debug('start new session')

        if in_session:
            defer.returnValue(None)

        in_session = True

        if arduino:
            #arduino.sendCommand(0x82, 0)
            #arduino.sendCommand(0x82, 1)
            arduino.sendCommand(0x82, 2)
            arduino.sendCommand(0x82, 3)

        countdown_delay = Config.getint('camera', 'countdown-delay')
        needed_captures = template.needed_captures(self.template)
        captures = 0
        errors = 0

        # PLUGINS
        p = self.plugins
        fc0 = p['FileCopy'].new(originals_path)
        fc1 = p['FileCopy'].new(composites_path)
        #fc3 = p['FileCopy'].new(thumbs_path)
        #fc4 = p['FileCopy'].new(details_path)
        #fc5 = p['FileCopy'].new(template_path)
        spool = p['FileCopy'].new(shared_path)

        #th0 = p['ImageThumb'].new(size='256x256', destination='thumbnail.png')
        #th1 = p['ImageThumb'].new(size='1024x1024', destination='thumbnail.png')

        cm = p['Composer'].new(self.template)
        #fd0 = p['FileDelete'].new()
        #fd1 = p['FileDelete'].new()

        filenames = list()

        while captures < needed_captures and errors < 3:
            try:
                filename = yield task.deferLater(reactor, countdown_delay,
                                                 self.capture)
            except:
                traceback.print_exc(file=sys.stdout)
                errors += 1
                logger.debug('failed capture %s/3', errors)
                task.deferLater(reactor, 0, error.play)
                task.deferLater(reactor, .15, error.play)
                task.deferLater(reactor, .30, error.play)
                continue

            captures += 1
            errors = 0
            logger.debug('successful capture (%s/%s)',
                         captures, needed_captures)

            if captures < needed_captures:
                finished.play()
            else:
                bell1.play()

            # C A L L B A C K S
            fn = filename
            original = yield fc0.process(fn)
            filenames.append(original)

            #thumb = yield th0.process(original)
            #thumb = yield fc3.process(thumb)
            #detail = yield th1.process(original)
            #detail = yield fc4.process(detail)

        if arduino:
            #arduino.sendCommand(0x81, 0)
            #arduino.sendCommand(0x81, 1)
            arduino.sendCommand(0x81, 2)
            arduino.sendCommand(0x81, 3)

        # composite
        d = cm.process(filenames.pop(0))
        d.addCallback(fc1.process)
        if Config.getboolean('kiosk', 'print'):
            d.addCallback(spool.process)
        for fn in filenames:
            cm.process(fn)

        in_session = False
        logger.debug('finished the session')


class Arduino(basic.LineReceiver):
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


class ServoServiceProtocol(basic.LineReceiver):
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


class ServoServiceFactory(protocol.ServerFactory):
    protocol = ServoServiceProtocol

    def __init__(self, arduino):
        self._arduino = arduino

    @property
    def arduino(self):
        return self._arduino


def new():
    import time
    global arduino

    # turn on all the relays on the arduino
    # the lights are wired on NC, so this turns lights off
    def lights_out():
        arduino.sendCommand(0x82, 0)
        arduino.sendCommand(0x82, 1)
        arduino.sendCommand(0x81, 2)
        arduino.sendCommand(0x81, 3)

    logger.debug('starting photo booth service')
    session = Session()

    # preview frame producer
    logger.debug('starting camera preview service')
    preview_port = 23453
    factory = protocol.Factory()
    factory.protocol = session.camera.create_producer
    reactor.listenTCP(preview_port, factory)

    # get the arduino going
    logger.debug('starting arduino')
    arduino = Arduino(session)
    try:
        s = SerialPort(arduino, Config.get('arduino', 'port'), reactor,
                       baudrate=Config.getint('arduino', 'baudrate'))
    except serial.serialutil.SerialException:
        raise

    # give arduino a couple seconds to be ready to accept data
    time.sleep(5)
    reactor.callWhenRunning(lights_out)

    # arduino servo tilt server
    logger.debug('starting tilt command listener')
    reactor.listenTCP(Config.getint('arduino', 'tcp-port'),
                      ServoServiceFactory(arduino))

    return reactor
