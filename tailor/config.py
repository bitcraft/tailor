# -*- coding: utf-8 -*-
import os.path
import configparser
import logging
import json

__all__ = ('Config',)

logger = logging.getLogger('tailor.config')

pkConfig = configparser.ConfigParser()


def jpath(*args):
    return os.path.normpath(os.path.join(*args))


def reload(path):
    config_path = jpath(path, 'config.ini')
    logger.debug('loading configuration: %s', config_path)
    pkConfig.read(config_path)

    app_root_path = os.path.realpath(os.path.join(__file__, '..', '..'))
    app_resources_path = jpath(app_root_path, 'tailor', 'resources')
    all_templates_path = jpath(app_resources_path, 'templates')
    all_images_path = pkConfig.get('paths', 'images')
    hot_print_folder = os.path.normpath(pkConfig['paths']['print-hot-folder'])

    # TODO: make sense of all the distributed config files
    import json
    with open(jpath(app_root_path, 'config', 'kiosk.json')) as fp:
        kiosk_cfg = json.loads(fp.read())
        pkConfig['kiosk'] = kiosk_cfg

    event_name = kiosk_cfg['event']['name']
    event_template = kiosk_cfg['event']['template']
    event_images_path = jpath(all_images_path, event_name)

    # TODO: eventually incorperate zeroconf discovery
    paths = {
        'print_hot_folder': hot_print_folder,
        'app_root_path': app_root_path,
        'app_resources': app_resources_path,
        'app_sounds': jpath(app_resources_path, 'sounds'),
        'app_images': jpath(app_resources_path, 'images'),
        'app_templates': all_templates_path,
        'event_template': jpath(all_templates_path, event_template),
        'event_images': event_images_path,
        'event_originals': jpath(event_images_path, 'originals'),
        'event_composites': jpath(event_images_path, 'composites'),
        'event_prints': jpath(event_images_path, 'prints'),
    }
    pkConfig['paths'] = paths

    # TODO: move to more generic loader
    filename = 'config/server.json'
    with open(filename) as fp:
        server_cfg = json.load(fp)

    interface_config = server_cfg['interface']
    pkConfig['remote_server'] = {'protocol': 'http',
                                 'host': '127.0.0.1',
                                 'port': interface_config['port']}


reload(os.path.join(os.path.dirname(__file__), '..', 'config'))
