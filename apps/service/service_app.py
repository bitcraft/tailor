# -*- coding: utf-8 -*-
"""
controls camera
accepts booth inputs
plays sounds
prints
manages plugin workflow, basically
"""
import asyncio
import logging
import os
import pickle
from collections import namedtuple
from contextlib import ExitStack
from functools import partial

from apps.service.session import Session
from tailor import plugins
from tailor.builder import JSONTemplateBuilder
from tailor.config import pkConfig
from tailor.zc import zc_service_context, load_services_from_config

logger = logging.getLogger("tailor.service")

# set ProactorEventLoop, to support subprocess on Windows OS
if os.name == 'nt':
    asyncio.set_event_loop(asyncio.ProactorEventLoop())

# used to create a dummy session when app is first started
mock_session = namedtuple('mock_session', 'countdown_value started finished idle')


class ServiceApp:
    """
    implements the application
    """

    def __init__(self):
        self.running = False
        self.running_tasks = list()
        self.template_filename = None
        self.session = mock_session(0, False, False, False)

    def run(self):
        self.running = True
        self.template_filename = pkConfig['paths']['event_template']
        self.make_folders()            # build folder structure to store photos
        loop = asyncio.get_event_loop()

        # camera

        # try:
        #     camera = plugins.shutter_camera.ShutterCamera()
        # except AttributeError:
        #     camera = plugins.opencv_camera.OpenCVCamera(0)

        camera = plugins.dummy_camera.DummyCamera()

        # arduino
        # serial_device = AsyncSerial()
        # serial_device = SelectSerial()
        # board = Board(serial_device)
        board = None

        # ExitStack is used to gracefully close the camera and other services we open
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

            # the servers defined below will not keep asyncio.wait from
            # thinking they are done.  meaning, without this pause,
            # aysncio will happily kill the server before any clients
            # have connected.
            # this delay task is added to prevent the app from closing before
            # clients have connected.
            # TODO: let servers wait indefinitely.
            task = loop.create_task(asyncio.sleep(18000))
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

            # loop.run_until_complete(task)
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

    @asyncio.coroutine
    def camera_preview_threaded_queue(self, camera, reader, writer):
        image = yield from camera.download_preview()
        packet = {
            'session': {
                'idle': self.session.idle,
                'started': self.session.started,
                'finished': self.session.finished,
                'timer_value': self.session.countdown_value,
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
