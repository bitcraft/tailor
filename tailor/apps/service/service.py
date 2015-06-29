"""
controls camera
accepts booth inputs
plays sounds
prints
manages plugin workflow, basically
"""
import asyncio
import os
import traceback
import logging
import sys

from tailor import plugins
from tailor.apps.service.service_zc import zeroconf_service
from tailor.builder import JSONTemplateBuilder
import tailor.plugins.composer.composer

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("tailor.service")


# set ProactorEventLoop, to support subprocess on Windows OS
if os.name == 'nt':
    asyncio.set_event_loop(asyncio.ProactorEventLoop())


class ServiceApp:
    """
    implements the application
    """

    def run(self):
        with zeroconf_service():
            template_filename = 'tailor/resources/templates/test_template.json'
            template = JSONTemplateBuilder().read(template_filename)
            loop = asyncio.get_event_loop()
            session = Session()
            loop.run_until_complete(session.start(template))


class Session:
    # def trigger_capture(self):
    #     """ set an event to trigger later, causing a capture
    #
    #     triggers are used to ensure capture events happen at
    #     regular intervals, without being affected by the time
    #     involved with capturing an image
    #
    #     :return: asyncio.Handle
    #     """
    #     loop = asyncio.get_event_loop()
    #     interval = pkConfig.getint('camera', 'countdown-interval')
    #     return loop.call_later(interval, self.capture)

    def __init__(self):
        pass

    def on_countdown_tick(self):
        # play sound or something
        pass

    @asyncio.coroutine
    def countdown(self, duration):
        """ countdown from whole seconds
        """
        duration = int(duration)
        for i in range(duration):
            self.on_countdown_tick()
            yield from asyncio.sleep(1)

    @asyncio.coroutine
    def start(self, template):
        """ new session

        Take 4 photos
        Each photo has 3 attempts to take a photo
        If we get 4 photos, or 3 failed attempts, then exit
        """
        logger.debug('starting new session')

        camera = plugins.dummy_camera.DummyCamera()

        # needed_captures = template_graph.needed_captures()
        needed_captures = 4
        captures = 0
        errors = 0

        while captures < needed_captures and errors < 3:
            # wait time_interval seconds
            yield from asyncio.sleep(1)
            yield from self.countdown(3)

            try:
                image = yield from camera.download_capture()
            except:
                errors += 1
                traceback.print_exc(file=sys.stdout)
                logger.debug('failed capture %s/3', errors)
                continue

            captures += 1
            errors = 0
            logger.debug('capture (%s/%s)', captures, needed_captures)

            # C A L L B A C K S
            template.push_image(image)
