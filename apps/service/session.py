# -*- coding: utf-8 -*-
import asyncio
import logging
import os
import sys
import re
import traceback
import threading

import pygame

from apps.service.async_helpers import *
from tailor import plugins
from tailor.config import pkConfig
from tailor.plugins.composer import TemplateRenderer

logger = logging.getLogger("tailor.service")

pygame.init()
pygame.mixer.init()

bell0 = pygame.mixer.Sound('tailor/resources/sounds/bell.wav')
bell1 = pygame.mixer.Sound('tailor/resources/sounds/long_bell.wav')
finished = pygame.mixer.Sound('tailor/resources/sounds/whistle.wav')

regex = re.compile('^(.*?)-(\d+)$')


def incremental_naming(path):
    basename = os.path.basename(path)
    root, ext = os.path.splitext(path)

    match = regex.match(root)
    if match:
        root, i = match.groups()
        i = int(i)
    else:
        i = 0

    while os.path.exists(path):
        i += 1
        filename = "{0}-{1:04d}{2}".format(root, i, ext)
        path = os.path.join(basename, filename)
        if i > 9999:
            raise RuntimeError

    return path


class Session:
    countdown_time = 5
    extra_wait_time = 5
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
        self.started = True
        errors = 0
        needed_captures = 4
        image_stack = list()
        small_size = 200, 500

        original_filename = 'original-0000.png'
        composite_filename = 'composite-0000.png'

        paths = pkConfig['paths']
        originals_folder = paths['event_originals']
        composites_folder = paths['event_composites']
        prints_folder = paths['event_prints']
        shared_folder = paths['print_hot_folder']

        join = os.path.join
        composite_path = incremental_naming(
            join(composites_folder, 'original', composite_filename))

        composite_small_path = incremental_naming(
            join(composites_folder, 'small', composite_filename))

        print_path = incremental_naming(
            join(prints_folder, composite_filename))

        timing = timing_generator(self.countdown_time, needed_captures,
                                  self.countdown_time + self.extra_wait_time)

        # eventually, defer task mgmt to something else...
        # perhaps a built-in i'm unaware of?...probably
        save_tasks = []

        for final, wait_time in timing:
            logger.debug('waiting %s seconds', wait_time)

            yield from self.countdown(wait_time)

            try:
                image = yield from camera.download_capture()
            except:
                errors += 1
                traceback.print_exc(file=sys.stdout)
                logger.debug('failed capture %s/3', errors)
                continue

            self.finished = final

            errors = 0

            # sound to indicate that session is closed
            if final:
                bell1.play()
            else:
                finished.play()

            # indicate that picture is taken, getting ready for next
            self.idle = True

            # add images to stack that will be used to create template
            image_stack.append(image)

            # async save the image
            # TODO: handle exceptions here somehow (usually when file cannot be saved)
            original_path = incremental_naming(
                join(originals_folder, 'original', original_filename))

            logger.debug('saving camera output to %s', original_path)
            yield from async_save(image, original_path)
            # save_tasks.append(task)

            # give camera some time to process exposure (may not be needed)
            yield from asyncio.sleep(self.time_to_wait_after_capture)

            self.idle = False

        # # prevent asyncio from complaining that exceptions are not caught
        # # not sure this is the best way to handle it
        # for task in save_tasks:
        #     try:
        #         exp = task.exception()
        #         if exp is not None:
        #             print(exp)
        #     except asyncio.futures.InvalidStateError:
        #         pass
        #
        # # make sure all files have saved to disk before continuing
        # yield from asyncio.wait(save_tasks)

        # add images to the template for rendering
        for image in image_stack:
            root.push_image(image)

        # render the template
        renderer = TemplateRenderer()
        composite = yield from renderer.render_all(root)

        # tasks will be run concurrently via threads
        # yield from asyncio.wait([
        yield from async_save(composite, composite_path)
        yield from async_thumbnail(composite, small_size, composite_small_path)
        yield from async_double(composite, print_path)
        # ])

        # print the double
        fc = plugins.filesystem.FileCopy(shared_folder)
        yield from fc.process(print_path)

        return root
