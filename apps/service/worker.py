# -*- coding: utf-8 -*-
from PIL import Image

from tailor.config import pkConfig


def make_image(data):
    # mode, size, data = data
    return Image.frombytes(*data)


def save_image(image, filename):
    image.save(filename,
               compression=pkConfig['compositor']['compression'])


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
    func_table = {i.__name__: i for i in (save, thumbnail, double)}

    # start our task queue worker
    item = queue.get()
    while item is not None:
        task, data, args = item       # split task name and the payload
        func_table[task](data, args)  # execute task with data
        queue.task_done()       # mark done so queue can be joined
        item = queue.get()      # wait for a new task

    queue.task_done()
