__all__ = ('sounds', 'images', 'music', 'load', 'loaded')

import os
import logging

import pygame
from tailor.config import pkConfig

logger = logging.getLogger('tailor.resources')

# because i am lazy
jpath = os.path.join

loaded = False
sounds = None
images = None
music = None


def load(resource_path):
    global sounds, images, music, loaded

    if loaded:
        logger.debug('want to load resources, but already have')
        return

    logger.debug('loading resources...')

    sounds = dict()
    images = dict()
    music = dict()

    if pkConfig.has_section('sound-files'):
        vol = pkConfig.getint('sound', 'sound-volume') / 100.
        for name, filename in pkConfig.items('sound-files'):
            path = jpath(resource_path, 'sounds', filename)
            logger.info('loading %s', path)
            sound = pygame.mixer.Sound(path)
            sound.set_volume(vol)
            sounds[name] = sound

    if pkConfig.has_section('app_images'):
        for name, filename in pkConfig.items('app_images'):
            path = jpath(resource_path, 'images', filename)
            logger.info('loading %s', path)
            # image = pygame.image.load(path)
            # images[name] = image

    if pkConfig.has_section('music-files'):
        for name, filename in pkConfig.items('music-files'):
            path = jpath(resource_path, 'music', filename)
            logger.info('loading %s', path)
            music[name] = path

    loaded = True


def play_music(name):
    try:
        track = music[name]
        logger.info('playing %s', track)
        vol = pkConfig.getint('sound', 'music-volume') / 100.
        if vol > 0:
            pygame.mixer.music.set_volume(vol)
            pygame.mixer.music.load(track)
            pygame.mixer.music.play(-1)
    except pygame.error:
        pass
