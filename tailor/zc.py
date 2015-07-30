import socket
import json
from contextlib import contextmanager

from zeroconf import ServiceInfo, Zeroconf

__all__ = [
    'zc_service_context',
    'load_services_from_json']


config = dict()


@contextmanager
def zc_service_context(service_info):
    zeroconf = Zeroconf()
    zeroconf.register_service(service_info)
    try:
        yield
    except:
        raise
    finally:
        zeroconf.unregister_service(service_info)
        zeroconf.close()


def new_service_from_json(service_data):
    service_config = service_data['config']
    type_name = service_config['type']
    desc_label = service_config['description'] + '.' + type_name

    addr = socket.inet_aton(config['host'])
    port = int(config['port'])

    properties = service_config['properties']

    return ServiceInfo(type_name, desc_label, addr, port, 0, 0, properties)


def load_services_from_config():
    # TODO: move to more generic loader
    filename = 'config/server.json'
    with open(filename) as fp:
        json_data = json.load(fp)

    interface_config = json_data['interface']
    config['host'] = interface_config['host']
    config['port'] = interface_config['port']

    for service_data in json_data['zeroconf-servers']:
        yield new_service_from_json(service_data)
