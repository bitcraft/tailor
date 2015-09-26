# -*- coding: utf-8 -*-
"""
controls camera
accepts booth inputs
plays sounds
prints
manages plugin workflow, basically
"""
import asyncio
import os
import logging
from contextlib import ExitStack
from functools import partial
import pickle

import pygame

from apps.service.session import Session
from tailor import plugins
from tailor.zc import zc_service_context, load_services_from_config
from tailor.builder import JSONTemplateBuilder
from tailor.config import pkConfig

logger = logging.getLogger("tailor.service")


# set ProactorEventLoop, to support subprocess on Windows OS
if os.name == 'nt':
    asyncio.set_event_loop(asyncio.ProactorEventLoop())


class ServiceApp:
    """
    implements the application
    """

    def __init__(self):
        self.running = False
        self.running_tasks = list()
        self.template_filename = None
        self.session = None

    def run(self):
        self.running = True
        self.template_filename = 'tailor/resources/templates/test_template.json'
        loop = asyncio.get_event_loop()

        # build folder strucutre to store photos
        task = loop.run_in_executor(None, self.make_folders)

        # camera
        # camera = plugins.dummy_camera.DummyCamera()
        try:
            camera = plugins.shutter_camera.ShutterCamera()
        except AttributeError:
            camera = plugins.opencv_camera.OpenCVCamera(0)

        # arduino
        # serial_device = AsyncSerial()
        # serial_device = SelectSerial()
        # board = Board(serial_device)
        board = None

        with ExitStack() as stack:
            stack.enter_context(camera)
            for service_info in load_services_from_config():
                context = zc_service_context(service_info)
                stack.enter_context(context)

            if board:
                task = loop.create_task(
                    self.wait_for_trigger(board.wait_for_packet(), camera))
                self.running_tasks.append(task)

            # debug.  must be started after the session is started
            # task = loop.create_task(self.update_camera_preview_pygame(camera))
            # self.running_tasks.append(task)

            task = loop.create_task(asyncio.sleep(3000))
            self.running_tasks.append(task)

            # serve previews in highly inefficient manner
            func = partial(self.camera_preview_threaded_queue, camera)
            coro = asyncio.start_server(func, '127.0.0.1', 22222, loop=loop)
            task = loop.create_task(coro)
            self.running_tasks.append(task)

            func = partial(self.wait_for_socket_open_trigger, camera)
            coro = asyncio.start_server(func, '127.0.0.1', 22223, loop=loop)
            task = loop.create_task(coro)
            self.running_tasks.append(task)

            # this try/except will need to be addressed as i learn about
            # futures and how they respond to being canceled.
            try:
                loop.run_until_complete(asyncio.wait(self.running_tasks))
            except asyncio.CancelledError:
                print('cancellation error was raised')
                pass

    @staticmethod
    def make_folders():
        # make sure directory structure is usable
        names = 'event_prints event_originals event_composites'
        for folder_name in names.split():
            path = pkConfig['paths'][folder_name]
            path = os.path.normpath(path)
            os.makedirs(path, mode=0o777, exist_ok=True)

        names = 'event_originals event_composites'
        for folder_name in names.split():
            for modifier in 'small original'.split():
                path = pkConfig['paths'][folder_name]
                path = os.path.join(path, modifier)
                path = os.path.normpath(path)
                os.makedirs(path, mode=0o777, exist_ok=True)

        os.makedirs(pkConfig['paths']['print_hot_folder'],
                    mode=0o777,
                    exist_ok=True)

    @asyncio.coroutine
    def wait_for_trigger(self, future, camera):
        yield from future

        template_graph_root = JSONTemplateBuilder().read(self.template_filename)
        self.session = Session()
        task = self.session.start(camera, template_graph_root)

        yield from task
        self.running = False

    @asyncio.coroutine
    def wait_for_socket_open_trigger(self, camera, reader, writer):
        # drop the connection right away
        writer.close()

        template_graph_root = JSONTemplateBuilder().read(self.template_filename)
        self.session = Session()
        task = self.session.start(camera, template_graph_root)

        yield from task
        self.running = False
        self.session = None

    @asyncio.coroutine
    def camera_preview_threaded_queue(self, camera, reader, writer):
        if self.session:
            countdown_value = self.session.countdown_value
            finished = self.session.finished
            started = self.session.started
            idle = self.session.idle
        else:
            started = False
            finished = False
            idle = False
            countdown_value = 0

        image = yield from camera.download_preview()
        packet = {
            'session': {
                'idle': idle,
                'started': started,
                'finished': finished,
                'timer_value': countdown_value,
            },
            'image_data': {
                'size': image.size,
                'mode': image.mode,
                'data': image.tobytes()
            }
        }
        data = pickle.dumps(packet, -1)
        writer.write(data)
        yield from writer.drain()
        writer.close()

    @asyncio.coroutine
    def update_camera_preview_pygame(self, camera):
        # run in thread because we don't want it to block the asyncio event loop

        def update_preview():
            global countdown_image

            screen_rect = screen.get_rect()
            image = pygame.image.fromstring(frame.tobytes(), frame.size,
                                            frame.mode).convert()
            image_rect = image.get_rect(center=screen_rect.center).fit(
                screen_rect)
            image = pygame.transform.scale(image, image_rect.size)
            # pygame.event.pump()

            if self.session.countdown_value_changed.is_set():
                if self.session.countdown_value:
                    countdown_image = font.render(
                        str(self.session.countdown_value), 1, (255, 255, 255))
                    countdown_image = countdown_image.convert_alpha()
                    self.session.countdown_value_changed.clear()

                screen.fill(0)
                screen.blit(countdown_image, image_rect.topright)

            # HACK TO SHOW LAST CAPTURE
            screen.blit(image, (0, 0))
            pygame.display.flip()

        pygame.init()

        # DEBUG!  Move to some kind of gui later (kivy?)
        filename = 'tailor/resources/fonts/Market_Deco.ttf'
        font = pygame.font.Font(filename, 300)
        countdown_image = None

        screen = pygame.display.set_mode((1280, 720))  # , pygame.FULLSCREEN)
        pygame.display.set_caption('camera display')
        loop = asyncio.get_event_loop()
        while self.running:
            # debug!  move to something else later
            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    self.running = False
                    for task in self.running_tasks:
                        print('closing running task:', task)
                        task.cancel()

            if self.session is None:
                yield from asyncio.sleep(.5)
                continue

            frame = yield from camera.download_preview()
            yield from loop.run_in_executor(None, update_preview)
