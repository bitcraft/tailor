# -*- coding: utf-8 -*-
"""

countdown between images
submits tasks to be processed by mp queue

"""
import asyncio
import logging
import multiprocessing as mp
import sys
import threading
import traceback
import re
import os
from io import BytesIO
from os import cpu_count
from os.path import join

import pygame
import requests
from PIL import Image

from apps.service.async_helpers import timing_generator
from apps.service.worker import run_worker
from tailor.config import pkConfig
from tailor.plugins.composer import TemplateRenderer

logger = logging.getLogger("tailor.service")

# reduce lookups in to the PIL package namespace
pil_open = Image.open

# make sure pygame sound lib is working
pygame.init()
pygame.mixer.init()

bell0 = pygame.mixer.Sound('tailor/resources/sounds/bell.wav')
bell1 = pygame.mixer.Sound('tailor/resources/sounds/long_bell.wav')
finished = pygame.mixer.Sound('tailor/resources/sounds/whistle.wav')


class Session:
    def __init__(self):
        self.countdown_value = 0
        self.countdown_value_changed = threading.Event()
        self.finished = False
        self.started = False
        self.idle = False

    @staticmethod
    def deconstruct_image(image):
        # return objects suitable for pickle/marshal/serialization
        return image.mode, image.size, image.tobytes()

    async def countdown(self, duration):
        """ countdown from whole seconds
        """
        duration = int(duration)
        for i in range(duration):
            self.countdown_value = duration - i
            if self.countdown_value < 4:
                bell0.play()
            await asyncio.sleep(1)

        self.countdown_value = 0

    def queue_image_save(self, image, filename):
        data = self.deconstruct_image(image)
        self.mp_queue.put(("save", data, (filename,)))

    def queue_image_thumbnail(self, image, filename):
        small_size = 200, 500
        data = self.deconstruct_image(image)
        self.mp_queue.put(("thumbnail", data, (small_size, filename,)))

    def queue_image_double(self, image, filename):
        data = self.deconstruct_image(image)
        self.mp_queue.put(("double", data, (filename,)))

    def queue_data_save(self, data, filename):
        self.mp_queue.put(("data save", data, filename))

    async def render_template(self, root):
        """
        
        :param root: 
        :return: Image
        """
        # render the composite image (async)
        renderer = TemplateRenderer()
        composite = await renderer.render_all(root)
        return composite

    def start_workers(self):
        # not using pool because it would be slower on windows
        # since processes cannot fork, there will always be a fixed
        # amount of time for an interpreter to spin up.
        # use 'spawn' for predictable cross-platform use
        def start_worker():
            worker = cxt.Process(target=run_worker, args=(self.mp_queue,))
            worker.daemon = True
            worker.start()
            return worker

        cxt = mp.get_context('spawn')
        self.mp_queue = cxt.JoinableQueue()
        self.mp_workers = [start_worker() for i in range(cpu_count())]

    def wait_for_workers(self):
        # TODO: not block here with sync api?
        for i in self.mp_workers:
            self.mp_queue.put(None)  # signal the workers to stop
        self.mp_queue.join()

    @staticmethod
    def format_number(id):
        return '{:05d}'.format(id)

    def guess_image_extension(self, ext=None):
        """ Get best guess file extension for the image
        
        :param ext: 
        :return: 
        """
        if ext is None:
            return pkConfig['compositor']['filetype']

        # TODO: something better!
        return 'jpg'

    def name_image(self, prefix, session, capture, ext=None):
        """ Generate name for individual images
        
        :param prefix: 
        :param session: 
        :param capture: 
        :return: 
        """
        ext = self.guess_image_extension(ext)

        return '{}-{}-{}.{}'.format(prefix,
                                    self.format_number(session),
                                    self.format_number(capture),
                                    ext)

    def name_composite(self, prefix, session, ext=None):
        """ Generate name for composite images
        
        :param prefix: 
        :param session: 
        :return: 
        """
        ext = self.guess_image_extension(ext)

        return '{}-{}.{}'.format(prefix,
                                 self.format_number(session),
                                 ext)

    def capture_path(self, session_id, capture_id):
        paths = pkConfig['paths']

        return join(paths['event_originals'],
                    'original',
                    self.name_image('original', session_id, capture_id))

    @staticmethod
    def determine_initial_capture_id():
        """ ...
        
        :return: 
        """
        # here be dragons
        regex = re.compile('^(.*?)-(\d+)$')

        try:
            with open(pkConfig['paths']['event_log']) as fp:
                for line in fp:
                    pass
                root, ext = os.path.splitext(line)
                match = regex.match(root)
                if match:
                    root, i = match.groups()
                    return int(i) + 1
                else:
                    return 0
        except IOError:
            return 0

    @staticmethod
    def mark_session_complete(filename):
        def mark():
            with open(pkConfig['paths']['event_log'], 'a') as fp:
                fp.write(filename + '\n')

        # TODO: make sure can fail eventually
        done = False
        while not done:
            try:
                mark()
                done = True
            except IOError:
                pass

    @staticmethod
    def convert_raw_to_pil(raw):
        return pil_open(BytesIO(raw))

    @staticmethod
    def play_capture_sound(final=False):
        if final:
            bell1.play()           # sound to indicate that session is closed
        else:
            finished.play()        # sound to indicate that photo was taken

    def get_timer(self, needed_captures):
        """ Get generator used to wait between captures
        
        :param needed_captures: number of images needed to capture
        :rtype: generator
        """
        # TODO: load from config
        countdown_time = 10
        extra_wait_time = 5

        return timing_generator(countdown_time, needed_captures,
                                countdown_time + extra_wait_time)

    async def start(self, camera, root):
        """ new session

        Take 4 photos
        Each photo has 3 attempts to take a photo
        If we get 4 photos, or 3 failed attempts, then exit

        :param root: template graph
        :param camera: camera object
        """
        logger.debug('starting new session')

        self.start_workers()  # each worker is a separate python process
        self.started = True

        needed_captures = root.needed_captures()
        session_id = self.determine_initial_capture_id()
        capture_id = 0
        errors = 0

        for final, wait_time in self.get_timer(needed_captures):
            await self.countdown(wait_time)

            try:
                # this image will be whatever format the camera is set to
                raw_image = await camera.download_capture()
            except:
                errors += 1
                traceback.print_exc(file=sys.stdout)
                logger.debug('failed capture %s/3', errors)
                continue

            self.idle = True           # indicate that picture is taken, getting ready for next
            self.finished = final      # indicate that the session has all required photos
            errors = 0                 # reset errors after each successful capture
            capture_id += 1

            # the template renderer expects to use pillow images
            # add images to the template for rendering
            image = self.convert_raw_to_pil(raw_image)
            root.push_image(image)

            # save the image as it was returned from the camera
            self.queue_data_save(raw_image, None)

            # give camera some fixed time to process exposure (may not be needed)
            # TODO: get from config
            time_to_wait_after_capture = 3
            await asyncio.sleep(time_to_wait_after_capture)

            self.idle = False          # indicate that the camera is now busy

        composite = await self.render_template(root)

        paths = pkConfig['paths']
        composites_folder = paths['event_composites']
        composite_filename = self.name_composite('composite', session_id)
        composite_path = join(composites_folder, 'original', composite_filename)
        composite_small_path = join(composites_folder, 'small', composite_filename)
        print_path = join(paths['event_prints'], composite_filename)

        self.queue_image_save(composite, composite_path)
        self.queue_image_thumbnail(composite, composite_small_path)
        self.queue_image_double(composite, print_path)

        self.wait_for_workers()  # blocking!

        # print the double
        # TODO: not use the http service?
        url = 'http://localhost:5000/print/' + composite_filename
        requests.get(url)

        self.mark_session_complete(composite_filename)

        return root
