import os.path
import configparser
import logging

__all__ = ('Config',)

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('tailor.config')

pkConfig = configparser.ConfigParser()


def reload(path):
    jpath = os.path.join
    config_path = jpath(path, 'config.ini')
    logger.debug('loading configuration: %s', config_path)
    pkConfig.read(config_path)

    app_root_path = os.path.realpath(os.path.join(__file__, '..', '..'))
    app_resources_path = jpath(app_root_path, 'tailor', 'resources')
    all_templates_path = jpath(app_resources_path, 'templates')
    all_images_path = pkConfig.get('paths', 'images')
    event_name = pkConfig.get('event', 'name')
    event_images_path = jpath(all_images_path, event_name)

    # TODO: eventually incorperate zeroconf discovery
    paths = {
        'app_resources': app_resources_path,
        'app_sounds': jpath(app_resources_path, 'sounds'),
        'app_images': jpath(app_resources_path, 'images'),
        'app_templates': all_templates_path,
        'event_template': jpath(all_templates_path,
                                pkConfig.get('event', 'template')),
        'event_images': event_images_path,
        'event_thumbs': jpath(event_images_path, 'thumbnails'),
        'event_details': jpath(event_images_path, 'detail'),
        'event_originals': jpath(event_images_path, 'originals'),
        'event_composites': jpath(event_images_path, 'composites'),
    }

    pkConfig['paths'] = paths
    pkConfig['remote_server'] = {'protocol': 'http',
                                 'host': '127.0.0.1',
                                 'port': 5000}


reload(os.path.join(os.path.dirname(__file__), '..', 'config'))
