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
import uvloop

from apps.service.session import Session
from tailor.plugins import get_camera
from tailor.builder import YamlTemplateBuilder
from tailor.config import pkConfig
from tailor.plugins.composer.filters.autocrop import Autocrop
from tailor.zc import load_services_from_config, zc_service_context

logger = logging.getLogger("tailor.service")

# use uvloop
asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

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
        self.make_folders()  # build folder structure to store photos
        loop = asyncio.get_event_loop()
        camera = get_camera()

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

    async def wait_for_trigger(self, future, camera):
        await future
        template_graph_root = YamlTemplateBuilder().read(self.template_filename)
        self.session = Session()
        await self.session.start(camera, template_graph_root)
        self.running = False

    async def wait_for_socket_open_trigger(self, camera, reader, writer):
        writer.close()  # drop the connection right away
        template_graph_root = YamlTemplateBuilder().read(self.template_filename)
        self.session = Session()
        await self.session.start(camera, template_graph_root)
        self.running = False

    async def camera_preview_threaded_queue(self, camera, reader, writer):
        """ Stream information and images to the kiosk process
        
        This streams cbor formatted 'packets' for information to a kiosk process.
        The kiosk generally lives on the same machine, but can be a remote computer.
        
        For the contents of each packet, look at the dictionary "data", below.
        Image data is a tuple that follows the PIL.Image object constructor, but is
        generic enough for any library to use.  It is simply size, mode, and pixels.
        
        :param camera: 
        :param reader: 
        :param writer: 
        :return: 
        """
        crop = Autocrop()
        import time

        while 1:
            start = time.time()
            image = await camera.download_preview()
            image = crop.process(image, (0, 0, 465 * 2, 435 * 2))

            # this is the data packet for the kiosk to read
            data = {
                'session': {
                    'idle': self.session.idle,
                    'started': self.session.started,
                    'finished': self.session.finished,
                    'timer_value': self.session.countdown_value,
                },
                'image_data': (image.size[0], image.size[1], image.mode, image.tobytes())
            }

            # format the pack for the wire
            payload = cbor.dumps(data)

            # prepend the length of the cbor data
            writer.write(struct.pack('Q', len(payload)))

            # send it over the wire
            writer.write(payload)

            # attempt to empty the buffer, may fail if other end hangs up
            try:
                await writer.drain()

            except (ConnectionResetError, ConnectionResetError, BrokenPipeError):
                writer.close()
                break

            print('finished frame drain', round((time.time() - start) * 100))

            # limit amount of frames sent
            await asyncio.sleep(1 / 60.)
