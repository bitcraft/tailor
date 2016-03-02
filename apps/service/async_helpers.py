# -*- coding: utf-8 -*-
import asyncio
from itertools import repeat

from PIL import Image
from PIL.Image import ANTIALIAS

from tailor.config import pkConfig


__all__ = [
    'timing_generator',
    'async_thumbnail',
    'async_save',
    'async_double'
]


def timing_generator(interval, amount, initial=None):
    """ Generator to make generic repeating timer

    Returns (bool, value) tuples, where:
            bool: if true, then this is last iteration of sequence
            value: ether interval or initial value

    :param interval: number to be returned each iteration
    :param amount:  number of iterations
    :param initial: if specified, this value will be used on 1st iteration
    :return: (bool, int)
    """
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
    def func():
        image.save(path, compression=pkConfig['compositor']['compression'])

    loop = asyncio.get_event_loop()
    coro = loop.run_in_executor(None, func)
    return coro


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
        _im.save(path,
                 compression=pkConfig['compositor']['compression'])

    loop = asyncio.get_event_loop()
    coro = loop.run_in_executor(None, func)
    return coro


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
        base.save(path,
                  compression=pkConfig['compositor']['compression'])

    loop = asyncio.get_event_loop()
    coro = loop.run_in_executor(None, func)
    return coro
