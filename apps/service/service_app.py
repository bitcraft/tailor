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
import struct
import os
from collections import namedtuple
from contextlib import ExitStack
from functools import partial

import cbor

from apps.service.session import Session
from tailor import plugins
from tailor.builder import JSONTemplateBuilder
from tailor.config import pkConfig
from tailor.zc import load_services_from_config, zc_service_context

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

    @staticmethod
    def get_camera():
        # camera
        camera_cfg = pkConfig['camera']
        camera_plugin = camera_cfg['plugin']
        # camera_name = camera_cfg['name']

        # TODO: Error handling
        if camera_plugin == "dummy":
            camera = plugins.dummy_camera.DummyCamera()
        elif camera_plugin == "shutter":
            # if camera_name:
            #     import re
            #     regex = re.compile(camera_name)
            # else:
            #     regex = None
            # TODO: regex is broken because of a py3 bug w/shutter
            regex = None
            camera = plugins.shutter_camera.ShutterCamera(regex)
        elif camera_plugin == "opencv":
            camera = plugins.opencv_camera.OpenCVCamera()
        elif camera_plugin == "pygame":
            camera = plugins.pygame_camera.PygameCamera()
        else:
            print("cannot find camera plugin")
            raise RuntimeError

        return camera

    def run(self):
        self.running = True
        self.template_filename = pkConfig['paths']['event_template']
        self.make_folders()            # build folder structure to store photos
        loop = asyncio.get_event_loop()
        camera = self.get_camera()

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
            # WARNING: this line will cause the program to eventually close
            task = loop.create_task(asyncio.sleep(26000))
            self.running_tasks.append(task)

            # serve previews in highly inefficient manner
            # asyncio streaming protocol
            # https://docs.python.org/3/library/asyncio-stream.html
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
        while 1:
            image = yield from camera.download_preview()
            data = {
                'session': {
                    'idle': self.session.idle,
                    'started': self.session.started,
                    'finished': self.session.finished,
                    'timer_value': self.session.countdown_value,
                },
                'image_data': (image.size[0], image.size[1], image.mode.lower(), image.tobytes())
            }
            payload = cbor.dumps(data)
            writer.write(struct.pack('Q', len(payload)))
            writer.write(payload)

            try:
                yield from writer.drain()
            except ConnectionResetError:
                writer.close()
                break

            yield from asyncio.sleep(1 / 60.)
