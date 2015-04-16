__all__ = ('Config',)

import os.path
import configparser
import logging
# import importlib


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('tailor.config')

Config = configparser.ConfigParser()


def reload(path):
    path = os.path.join(path, 'config.ini')
    logger.debug('loading configuration: %s', path)
    Config.read(path)


reload(os.path.join(os.path.dirname(__file__), '..', 'config'))
# importlib.import_module('config')
