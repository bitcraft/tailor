#!/usr/bin/env python
"""
display the camera's live preview using pygame.
uses threads for speed
suitable for any display that is compatible with SDL (framebuffers, etc)
"""

import threading
import time
import queue
from io import StringIO

import pygame
import shutter


class CaptureThread(threading.Thread):
    def __init__(self, queue, camera, lock):
        super(CaptureThread, self).__init__()
        self.queue = queue
        self.camera = camera
        self.lock = lock
        self._running = False

    def stop(self):
        self._running = False

    def run(self):
        self._running = True
        preview = self.camera.capture_preview
        put = self.queue.put
        lock = self.lock
        while self._running:
            with lock:
                data = preview().get_data()
            put(data)


class BlitThread(threading.Thread):
    def __init__(self, queue, surface, lock):
        super(BlitThread, self).__init__()
        self.queue = queue
        self.surface = surface
        self.lock = lock
        self._running = False

    def stop(self):
        self._running = False

    def run(self):
        self._running = True
        get = self.queue.get
        load = pygame.image.load
        scale = pygame.transform.scale
        screen = self.surface
        size = self.surface.get_size()
        lock = self.lock
        while self._running:
            image = load(StringIO(get())).convert()
            with lock:
                scale(image, size, screen)


def quit_pressed():
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            return True
        elif event.type == pygame.KEYDOWN:
            return True
        elif event.type == pygame.MOUSEBUTTONDOWN:
            return True
    return False


if __name__ == '__main__':
    pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    main_surface = pygame.display.get_surface()

    pygame.mouse.set_visible(False)

    display_lock = threading.Lock()
    camera_lock = threading.Lock()
    queue = queue.Queue(10)
    camera = shutter.Camera()

    thread0 = CaptureThread(queue, camera, camera_lock)
    thread0.daemon = True
    thread0.start()

    thread1 = BlitThread(queue, main_surface, display_lock)
    thread1.daemon = True
    thread1.start()

    clock = pygame.time.Clock()
    flip = pygame.display.flip
    try:
        while not quit_pressed():
            with display_lock:
                flip()
            clock.tick(30)
    finally:
        thread0.stop()
        thread1.stop()
        time.sleep(1)
        camera.close()
