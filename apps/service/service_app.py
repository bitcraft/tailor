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
        #  task = loop.run_in_executor(None, self.make_folders)
        self.make_folders()

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

            # TODO: unify this board trigger and the packet trigger
            if board:
                task = loop.create_task(
                    self.wait_for_trigger(board.wait_for_packet(), camera))
                self.running_tasks.append(task)

            # required to give things time to start?  idk
            task = loop.create_task(asyncio.sleep(5000))
            self.running_tasks.append(task)

            # serve previews in highly inefficient manner
            func = partial(self.camera_preview_threaded_queue, camera)
            coro = asyncio.start_server(func, '127.0.0.1', 22222, loop=loop)
            task = loop.create_task(coro)
            self.running_tasks.append(task)

            # wait for a camera trigger in highly inefficient manner
            func = partial(self.wait_for_socket_open_trigger, camera)
            coro = asyncio.start_server(func, '127.0.0.1', 22223, loop=loop)
            task = loop.create_task(coro)
            self.running_tasks.append(task)

            # this try/except will need to be addressed as i learn about
            # futures and how they respond to being canceled.
            loop.run_until_complete(task)
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

