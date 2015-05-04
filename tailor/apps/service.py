#!/usr/bin/env python
"""
Controls camera and booth inputs
"""
import asyncio
import configparser
import os
import sys
import threading
import traceback
import logging
import pygame
import networkx as nx

from tailor import resources
from tailor import template
from tailor.config import pkConfig


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("tailor.service")


# set ProactorEventLoop, to support subprocess on Windows OS
if os.name == 'nt':
    asyncio.set_event_loop(asyncio.ProactorEventLoop())


class Booth:
    """
    implements the hardware interface to booth electronics
    """

    def enable_relay(self, index):
        pass

    def disable_relay(self, index):
        pass

    def set_camera_tilt(self, value):
        pass


class ServiceApp:
    """
    implements the application
    """

    def __init__(self):
        self.lock = threading.Lock()

    def run(self):
        pygame.mixer.init()
        resources.load(pkConfig['paths']['app_resources'])

        loop = asyncio.get_event_loop()
        session = Session()
        loop.run_until_complete(session.start())


class Session:
    def __init__(self):
        logger.debug('building new session...')

        self.template = configparser.ConfigParser()
        self.template.read(pkConfig['paths']['event_template'])
        self.workflow = None
        self.camera = None

        self.build_workflow()

    def scan_plugins(self):
        from yapsy.PluginManager import PluginManager




    def build_workflow(self):
        """
        workflow: camera must be node[0]

        :return:
        """
        self.scan_plugins()

        import tailor
        self.workflow = nx.Graph()

        camera = tailor.plugins.dummy_camera.DummyCamera()
        self.workflow.add_node(camera)
        self.camera = camera

    def trigger_capture(self):
        """ set an event to trigger later, causing a capture

        triggers are used to ensure capture events happen at
        regular intervals, without being affected by the time
        involved with capturing an image

        :return: asyncio.Handle
        """
        loop = asyncio.get_event_loop()
        interval = pkConfig.getint('camera', 'countdown-interval')
        return loop.call_later(interval, self.capture)

    @asyncio.coroutine
    def countdown(self, duration):
        """ countdown from whole seconds
        :return:
        """
        duration = int(duration)
        for i in range(duration):
            self.play_countdown_sound()
            yield from asyncio.sleep(1)

    @asyncio.coroutine
    def capture(self):
        """ get image from the camera

        :return:
        """
        yield self.camera.download_capture()

    @staticmethod
    def play_error_sound():
        loop = asyncio.get_event_loop()
        error = resources.sounds['error']
        loop.call_later(.15, error.play)
        loop.call_later(.30, error.play)
        loop.call_later(.45, error.play)

    @staticmethod
    def play_countdown_sound():
        resources.sounds['bell0'].play()

    @staticmethod
    def play_finished_sound():
        resources.sounds['finished'].play()

    @staticmethod
    def play_complete_sound():
        resources.sounds['bell'].play()

    @asyncio.coroutine
    def start(self):
        """ new session

        Take 4 photos
        Each photo has 3 attempts to take a photo
        If we get 4 photos, or 3 failed attempts, then exit
        """
        logger.debug('start new session')

        needed_captures = template.needed_captures(self.template)
        interval = int(pkConfig['camera']['capture-interval'])
        captures = 0
        errors = 0

        while captures < needed_captures and errors < 3:
            # wait time_interval seconds
            yield from asyncio.sleep(1)
            yield from self.countdown(3)

            try:
                image = yield from self.capture()
            except:
                errors += 1
                traceback.print_exc(file=sys.stdout)
                logger.debug('failed capture %s/3', errors)
                self.play_error_sound()
                continue

            captures += 1
            errors = 0
            logger.debug('successful capture (%s/%s)', captures, needed_captures)

            if captures < needed_captures:
                self.play_finished_sound()
            else:
                self.play_complete_sound()

                # C A L L B A C K S
                # fn = filename
                # original = yield fc0.process(fn)
                # filenames.append(original)

        # TODO: composites

        logger.debug('finished the session')
