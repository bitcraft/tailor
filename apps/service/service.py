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
import pygame
from contextlib import ExitStack

from tailor import plugins
from tailor.zc import zc_service_context, load_services_from_config
from tailor.builder import JSONTemplateBuilder
from tailor.plugins.composer.renderer import TemplateRenderer

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

        # @asyncio.coroutine
        # def sessions_loop():
        #     while running:
        #         wait_for_trigger()
        #         image = from sessions()
        #         postin_image_to_server(image)

        # camera = plugins.dummy_camera.DummyCamera()
        camera = plugins.opencv_camera.OpenCVCamera()

        self.running = True
        task = loop.create_task(self.update_camera_preview_pygame(camera))

        with ExitStack() as stack:
            stack.enter_context(camera)
            for service_info in load_services_from_config():
                context = zc_service_context(service_info)
                stack.enter_context(context)

            session = session.start(camera, template_graph_root)
            loop.run_until_complete(session)

    @asyncio.coroutine
    def update_camera_preview_pygame(self, camera):
        # run in thread because we don't want it to block the asyncio event loop
        def update_preview():
            screen_rect = screen.get_rect()
            image = pygame.image.fromstring(frame.tobytes(), frame.size, frame.mode).convert()
            image_rect = image.get_rect(center=screen_rect.center).fit(screen_rect)
            image = pygame.transform.scale(image, image_rect.size)
            screen.blit(image, image_rect)
            pygame.display.flip()

        pygame.init()
        screen = pygame.display.set_mode((1280, 720), pygame.FULLSCREEN)
        pygame.display.set_caption('camera display')
        loop = asyncio.get_event_loop()
        while self.running:
            pygame.event.pump()
            frame = yield from camera.download_preview()
            yield from loop.run_in_executor(None, update_preview)
            yield from asyncio.sleep(.01)


class Session:
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
    def start(self, camera, root):
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

        image_stack = list()

        while captures < needed_captures and errors < 3:
            # wait time_interval seconds
            # yield from self.countdown(3)

            yield from asyncio.sleep(1)
            # yield from asyncio.sleep(500000)

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

            image_stack.append(image)

        # TODO: allow 'redo' of image...pop image off image stack and do again
        def redo_image():
            image_stack.pop()

        for image in image_stack:
            root.push_image(image)

        renderer = TemplateRenderer()
        yield from renderer.render_all_and_save(root, 'test_service.png')

        return root
