__all__ = ('Config',)

from six.moves import configparser
import os.path

Config = configparser.ConfigParser()


def reload(path):
    jpath = os.path.join
    Config.read(jpath(path, 'config.ini'))

reload(
    os.path.realpath(
        os.path.join(__file__, '..', '..', 'config')
    )
)