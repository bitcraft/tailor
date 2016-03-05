# -*- coding: utf-8 -*-
import asyncio
import logging
import multiprocessing as mp
import sys
import threading
import traceback
from os import cpu_count
from os.path import join

import pygame
import requests

from apps.service.async_helpers import timing_generator
from apps.service.worker import run_worker
from tailor.config import pkConfig
from tailor.plugins.composer import TemplateRenderer

logger = logging.getLogger("tailor.service")

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

        # TODO: load from config
        self.countdown_time = 10
        self.extra_wait_time = 5
        self.time_to_wait_after_capture = 3

    @asyncio.coroutine
    def countdown(self, duration):
        """ countdown from whole seconds
        """
        duration = int(duration)
        for i in range(duration):
            self.countdown_value = duration - i
            if self.countdown_value < 4:
                bell0.play()
            yield from asyncio.sleep(1)

        self.countdown_value = 0

    @staticmethod
    def deconstruct_image(image):
        # return objects suitable for pickle/marshal
        return image.mode, image.size, image.tobytes()

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

    @asyncio.coroutine
    def render_template(self, root):
        # render the composite image (async)
        renderer = TemplateRenderer()
        composite = yield from renderer.render_all(root)
        return composite

    def start_workers(self):
        # not using pool because it would be slower on windows
        # since processes cannot fork, there will always be a fixed
        # amount of time for an interpreter to spin up.
        # use 'spawn' for predictable cross-platform use
        cxt = mp.get_context('spawn')
        self.mp_queue = cxt.JoinableQueue()
        self.mp_workers = list()
        for i in range(cpu_count()):
            worker = cxt.Process(target=run_worker, args=(self.mp_queue,))
            worker.daemon = True
            worker.start()
            self.mp_workers.append(worker)

    def wait_for_workers(self):
        # TODO: not block here with sync api?
        # TODO: implement template-based doubler
        for i in self.mp_workers:
            self.mp_queue.put(None)  # signal the workers to stop
        self.mp_queue.join()

    @staticmethod
    def format_id(id):
        return '{:05d}'.format(id)

    def name_image(self, prefix, id):
        return '{}-{}.{}'.format(prefix, self.format_id(id),
                                 pkConfig['compositor']['filetype'])

    def determine_initial_capture_id(self):
        # here be dragons
        import re, os
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

    def mark_session_complete(self, filename):
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

    @asyncio.coroutine
    def start(self, camera, root):
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

        paths = pkConfig['paths']
        needed_captures = root.needed_captures()
        session_id = self.determine_initial_capture_id()
        capture_id = session_id

        # TODO: handle camera errors
        errors = 0
        timing = timing_generator(self.countdown_time, needed_captures,
                                  self.countdown_time + self.extra_wait_time)

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

            self.finished = final      # indicate that the session has all required photos
            errors = 0                 # reset errors after each successful capture
            capture_id += 1

            if final:
                bell1.play()           # sound to indicate that session is closed
            else:
                finished.play()        # sound to indicate that photo was taken

            self.idle = True           # indicate that picture is taken, getting ready for next
            root.push_image(image)     # add images to the template for rendering

            path = join(paths['event_originals'], self.name_image('original', capture_id))
            self.queue_image_save(image, path)  # add this image to the worker queue

            # give camera some fixed time to process exposure (may not be needed)
            yield from asyncio.sleep(self.time_to_wait_after_capture)

            self.idle = False          # indicate that the camera is now busy

        composite = yield from self.render_template(root)

        composites_folder = paths['event_composites']
        composite_filename = self.name_image('composite', session_id)

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
