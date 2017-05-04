# -*- coding: utf-8 -*-
import yaml
import logging
import os.path

__all__ = ('Config',)

logger = logging.getLogger('tailor.config')

pkConfig = dict()


def jpath(*args):
    return os.path.normpath(os.path.join(*args))


def reload(path):
    app_root_path = os.path.realpath(os.path.join(__file__, '..', '..'))

    # TODO: make sense of all the distributed config files
    with open(jpath(app_root_path, 'config', 'service.yaml')) as fp:
        service_cfg = yaml.load(fp)
        pkConfig.update(service_cfg)

    # TODO: make sense of all the distributed config files
    with open(jpath(app_root_path, 'config', 'kiosk.yaml')) as fp:
        kiosk_cfg = yaml.load(fp)
        pkConfig['kiosk'] = kiosk_cfg

    app_resources_path = jpath(app_root_path, 'tailor', 'resources')
    all_templates_path = jpath(app_resources_path, 'templates')
    all_images_path = pkConfig['paths']['images']

    event_name = kiosk_cfg['event']['name']
    event_template = kiosk_cfg['event']['template']
    event_images_path = jpath(all_images_path, event_name)

    # TODO: eventually incorporate zeroconf discovery
    paths = {
        'print_hot_folder': hot_print_folder,
        'app_root_path': app_root_path,
        'app_resources': app_resources_path,
        'app_sounds': jpath(app_resources_path, 'sounds'),
        'app_images': jpath(app_resources_path, 'images'),
        'app_templates': all_templates_path,
        'event_images': event_images_path,
        'event_log': jpath(event_images_path, 'sessions.log'),
        'event_template': jpath(all_templates_path, event_template),
        'event_originals': jpath(event_images_path, 'originals'),
        'event_composites': jpath(event_images_path, 'composites'),
        'event_prints': jpath(event_images_path, 'prints'),
    }
    pkConfig['paths'] = paths

    # TODO: move to more generic loader
    with open(jpath(app_root_path, 'config', 'server.yaml')) as fp:
        server_cfg = yaml.load(fp)

    interface_config = server_cfg['interface']
    pkConfig['server'] = server_cfg
    pkConfig['remote_server'] = {'protocol': 'http',
                                 'host': '127.0.0.1',
                                 'port': interface_config['port']}


reload(os.path.join(os.path.dirname(__file__), '..', 'config'))
