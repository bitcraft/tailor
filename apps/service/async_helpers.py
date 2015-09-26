# -*- coding: utf-8 -*-
import asyncio
from itertools import repeat

from PIL import Image
from PIL.Image import ANTIALIAS

__all__ = [
    'timing_generator',
    'async_thumbnail',
    'async_save',
    'async_double'
]


def timing_generator(interval, amount, initial=None):
    assert (amount > 0)

    if initial is not None:
        amount -= 1
        yield amount == 0, initial

    for index, value in enumerate(repeat(interval, amount), start=1):
        yield index == amount, value


def async_save(image, path):
    """ save image to filesystem

    :param image:
    :param path:
    :return:
    """
    loop = asyncio.get_event_loop()
    coro = loop.run_in_executor(None, image.save, path)
    return coro
    # return loop.create_task(coro)


def async_thumbnail(image, size, path):
    """ thumbnail a PIL image, save it, do not change original

    :param image:
    :param size:
    :param path:
    :return:
    """

    def func():
        _im = image.copy()
        _im.thumbnail(size, ANTIALIAS)
        _im.save(path)

    loop = asyncio.get_event_loop()
    coro = loop.run_in_executor(None, func)
    return coro
    # return loop.create_task(coro)


def async_double(image, path):
    """ double image, save it

    :param image:
    :param path:
    :return:
    """

    def func():
        base = Image.new('RGBA', (1200, 1800))
        areas = ((0, 0), (600, 0))
        for area in areas:
            base.paste(image, area, mask=image)
        base.save(path)

    loop = asyncio.get_event_loop()
    coro = loop.run_in_executor(None, func)
    return coro
    # return loop.create_task(coro)
