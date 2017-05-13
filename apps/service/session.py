# -*- coding: utf-8 -*-
"""

countdown between images
submits tasks to be processed by mp queue

"""
import asyncio
import logging
import sys
import threading
import traceback
import re
import os
from io import BytesIO
from os.path import join

import pygame
import requests
from PIL import Image

from apps.service.worker import WorkerPool
from apps.service.async_helpers import timing_generator
from tailor.config import pkConfig
from tailor.plugins.composer import TemplateRenderer

logger = logging.getLogger("tailor.service")

# reduce lookups in to the PIL package namespace
pil_open = Image.open

# make sure pygame sound lib is working
pygame.init()
pygame.mixer.init()


def load_sound(filename):
    path = join(pkConfig['paths']['app_sounds'], filename)
    return pygame.mixer.Sound(path)


class Session:
    def __init__(self):
        # the following attributes are used by the service_app,
        # which will read them and send that data to the kiosk.
        self.countdown_value_changed = threading.Event()
        self.countdown_value = 0
        self.finished = False
        self.started = False
        self.idle = False

        self.sounds = dict()
        for name, fn in pkConfig['sounds'].items():
            self.sounds[name] = load_sound(fn)

    async def countdown(self, duration):
        """ countdown from whole seconds
        """
        duration = int(duration)
        for i in range(duration):
            self.countdown_value = duration - i
            if self.countdown_value < 4:
                self.sounds['countdown-tick'].play()
            await asyncio.sleep(1)

        self.countdown_value = 0

    async def render_template(self, root):
        """
        
        :param root: 
        :return: Image
        """
        # render the composite image (async)
        renderer = TemplateRenderer()
        composite = await renderer.render_all(root)
        return composite

    @staticmethod
    def format_number(value):
        """
        
        :type value: int
        :return: str
        """
        return '{:05d}'.format(value)

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

    def capture_path(self, session_id, capture_id, ext=None):
        paths = pkConfig['paths']

        return join(paths['event_originals'],
                    'original',
                    self.name_image('original', session_id, capture_id, ext))

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

    def play_capture_sound(self, final=False):
        if final:
            self.sounds['finish-session'].play()
        else:
            self.sounds['finish-capture'].play()

    def get_timer(self, needed_captures):
        """ Get generator used to wait between captures
        
        :param needed_captures: number of images needed to capture
        :rtype: generator
        """
        countdown_time = pkConfig['session']['countdown-time']
        extra_wait_time = pkConfig['session']['extra-wait-time']

        return timing_generator(countdown_time, needed_captures,
                                countdown_time + extra_wait_time)

    async def start(self, camera, template_root):
        """ new session

        Take 4 photos
        Each photo has 3 attempts to take a photo
        If we get 4 photos, or 3 failed attempts, then exit

        :param template_root: template graph
        :param camera: camera object
        """
        logger.debug('starting new session')

        pool = WorkerPool()
        pool.start_workers()
        max_failures = pkConfig['session']['retries']

        self.started = True
        self.finished = False

        needed_captures = template_root.needed_captures()
        session_id = self.determine_initial_capture_id()

        for capture_id, timer in enumerate(self.get_timer(needed_captures)):
            final, wait_time = timer

            await self.countdown(wait_time)

            for attempt in range(max_failures):
                try:
                    raw_image = await camera.download_capture()
                    break
                except:
                    self.sounds['error'].play()
                    traceback.print_exc(file=sys.stdout)
                    logger.debug('failed capture %s/3', attempt)

            else:
                raise RuntimeError

            self.idle = True           # indicate that picture is taken, getting ready for next
            self.play_capture_sound(final)

            # the template renderer expects to use pillow images
            # add images to the template for rendering
            image = self.convert_raw_to_pil(raw_image)
            template_root.push_image(image)

            path = self.capture_path(session_id, capture_id, 'jpg')
            pool.queue_data_save(raw_image, path)

            self.idle = False          # indicate that the camera is not busy
            self.finished = final      # indicate that the session has all required photos

        paths = pkConfig['paths']
        composites_folder = paths['event_composites']
        composite_filename = self.name_composite('composite', session_id)
        composite_path = join(composites_folder, 'original', composite_filename)
        composite_small_path = join(composites_folder, 'small', composite_filename)
        print_path = join(paths['event_prints'], composite_filename)

        composite = await self.render_template(template_root)

        pool.queue_image_save(composite, composite_path)
        pool.queue_image_thumbnail(composite, composite_small_path)
        pool.queue_image_double(composite, print_path)
        pool.wait_for_workers()  # blocking!

        # print the double
        # TODO: not use the http service?
        url = 'http://localhost:5000/print/' + composite_filename
        requests.get(url)

        self.mark_session_complete(composite_filename)

        return template_root
