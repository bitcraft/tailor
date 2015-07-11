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
# from tailor.apps.service.service_zc import zeroconf_service
from tailor.builder import JSONTemplateBuilder
from tailor.plugins.composer.renderer import TemplateRenderer

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
        template_filename = 'tailor/resources/templates/test_template.json'
        template_graph_root = JSONTemplateBuilder().read(template_filename)
        loop = asyncio.get_event_loop()
        session = Session()
        loop.run_until_complete(session.start(template_graph_root))


class Session:
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
    def start(self, root):
        """ new session

        Take 4 photos
        Each photo has 3 attempts to take a photo
        If we get 4 photos, or 3 failed attempts, then exit
        """
        logger.debug('starting new session')

        # needed_captures = template_graph.needed_captures()
        needed_captures = 4
        captures = 0
        errors = 0

        # camera = plugins.dummy_camera.DummyCamera()
        camera = plugins.opencv_camera.OpenCVCamera()

        with camera:
            while captures < needed_captures and errors < 3:
                # wait time_interval seconds
                # yield from asyncio.sleep(1)
                # yield from self.countdown(3)

                try:
                    image = camera.download_capture()
                except:
                    errors += 1
                    traceback.print_exc(file=sys.stdout)
                    logger.debug('failed capture %s/3', errors)
                    continue

                captures += 1
                errors = 0
                logger.debug('capture (%s/%s)', captures, needed_captures)

                # C A L L B A C K S
                root.push_image(image)

        renderer = TemplateRenderer()
        image = renderer.render_all(root)
        image.save('test_service.png')
