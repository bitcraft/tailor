# -*- coding: utf-8 -*-
import asyncio
import logging
import os
import re
import sys
import threading
import traceback

import pygame
import requests

from apps.service.async_helpers import *
from tailor.config import pkConfig
from tailor.plugins.composer import TemplateRenderer
from tailor.plugins.filesystem import incremental_naming

logger = logging.getLogger("tailor.service")

pygame.init()
pygame.mixer.init()

bell0 = pygame.mixer.Sound('tailor/resources/sounds/bell.wav')
bell1 = pygame.mixer.Sound('tailor/resources/sounds/long_bell.wav')
finished = pygame.mixer.Sound('tailor/resources/sounds/whistle.wav')

regex = re.compile('^(.*?)-(\d+)$')


class Session:
    countdown_time = 1
    extra_wait_time = 1
    time_to_wait_after_capture = 3

    def __init__(self):
        self.countdown_value = 0
        self.countdown_value_changed = threading.Event()
        self.finished = False
        self.started = False
        self.idle = False

    def on_countdown_tick(self):
        if self.countdown_value < 4:
            bell0.play()

    @asyncio.coroutine
    def countdown(self, duration):
        """ countdown from whole seconds
        """
        duration = int(duration)
        for i in range(duration):
            self.countdown_value = duration - i
            self.on_countdown_tick()
            yield from asyncio.sleep(1)

        self.countdown_value = 0

    @asyncio.coroutine
    def start(self, camera, root):
        """ new session

        Take 4 photos
        Each photo has 3 attempts to take a photo
        If we get 4 photos, or 3 failed attempts, then exit
        """
        logger.debug('starting new session')

        # needed_captures = template_graph.needed_captures()
        # print(needed_captures)
        self.started = True
        errors = 0
        needed_captures = 4
        image_stack = list()
        small_size = 200, 500

        original_filename = 'original-0000.' + pkConfig['compositor']['filetype']
        composite_filename = 'composite-0000.' + pkConfig['compositor']['filetype']

        paths = pkConfig['paths']
        originals_folder = paths['event_originals']
        composites_folder = paths['event_composites']
        prints_folder = paths['event_prints']

        join = os.path.join
        composite_path = incremental_naming(
            join(composites_folder, 'original', composite_filename))

        composite_small_path = incremental_naming(
            join(composites_folder, 'small', composite_filename))

        print_path = incremental_naming(
            join(prints_folder, composite_filename))

        timing = timing_generator(self.countdown_time, needed_captures,
                                  self.countdown_time + self.extra_wait_time)

        for final, wait_time in timing:
            logger.debug('waiting %s seconds', wait_time)

            yield from self.countdown(wait_time)

            # begin_time = time.time()

            try:
                image = yield from camera.download_capture()
            except:
                errors += 1
                traceback.print_exc(file=sys.stdout)
                logger.debug('failed capture %s/3', errors)
                continue

            self.finished = final      # indicate that the session has all required photos

            errors = 0

            if final:
                bell1.play()           # sound to indicate that session is closed
            else:
                finished.play()        # sound to indicate that photo was taken

            self.idle = True           # indicate that picture is taken, getting ready for next

            image_stack.append(image)  # add images to stack used to create the template

            # give camera some time to process exposure (may not be needed)
            yield from asyncio.sleep(self.time_to_wait_after_capture)

            # process_time = time.time() - begin_time

            self.idle = False          # indicate that the camera is now busy

        # TODO: handle exceptions here: usually when file cannot be saved
        futures = list()
        for image in image_stack:
            # build a future that can be waited on to save files in threads
            original_path = incremental_naming(
                join(originals_folder, 'original', original_filename))
            logger.debug('saving camera output to %s', original_path)
            coro = async_save(image, original_path)
            futures.append(coro)

            # add images to the template for rendering
            root.push_image(image)

        loop = asyncio.get_event_loop()

        # add future for the composite image rendering
        renderer = TemplateRenderer()
        composite_future = asyncio.async(renderer.render_all(root))
        futures.append(composite_future)

        yield from asyncio.wait(futures)

        # tasks will be run concurrently via threads
        composite = composite_future.result()
        yield from asyncio.wait([
            async_save(composite, composite_path),
            async_thumbnail(composite, small_size, composite_small_path),
            async_double(composite, print_path)
        ])

        # print the double
        # TODO: implement template-based doubler
        filename = os.path.basename(print_path)
        url = 'http://localhost:5000/print/' + filename
        requests.get(url)

        return root
