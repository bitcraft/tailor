# -*- coding: utf-8 -*-
"""

operations for the mp queue

"""
from os import cpu_count
import multiprocessing as mp

from PIL import Image

from tailor.config import pkConfig


def make_image(data):
    # mode, size, data = data
    return Image.frombytes(*data)


def save_image(image, filename):
    kwargs = dict(pkConfig['compositor']['pil_options'])
    image.save(filename, **kwargs)


def write(data, filename):
    """
    
    :type data: bytes
    :type filename: str
    :rtype: None 
    """
    with open(filename, 'wb') as fp:
        fp.write(data)


def save(data, args):
    save_image(make_image(data), args[0])


def thumbnail(data, args):
    size, filename = args
    image = make_image(data)
    image.thumbnail(size, Image.ANTIALIAS)
    save_image(image, filename)


def double(data, args):
    image = make_image(data)
    base = Image.new('RGBA', (1200, 1800))
    areas = ((0, 0), (600, 0))
    for area in areas:
        base.paste(image, area, mask=image)
    save_image(base, args[0])


def run_worker(queue):
    func_table = {i.__name__: i for i in (save, thumbnail, double, write)}

    # start our task queue worker
    item = queue.get()

    while item is not None:
        task, data, args = item       # split task name and the payload
        func_table[task](data, args)  # execute task with data
        queue.task_done()             # mark done so queue can be joined
        item = queue.get()            # wait for a new task

    queue.task_done()


class WorkerPool:
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
    def deconstruct_image(image):
        # return objects suitable for pickle/marshal/serialization
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

    def queue_data_save(self, data, filename):
        self.mp_queue.put(("data save", data, (filename,)))
