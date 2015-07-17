import socket
from contextlib import contextmanager

from zeroconf import ServiceInfo, Zeroconf


@contextmanager
def zv_service_context(type_name, desc, properties, addr, port):
    desc_label = desc + '.' + type_name

    info = ServiceInfo(type_name, desc_label,
                       socket.inet_aton(addr), port, 0, 0,
                       properties)

    zeroconf = Zeroconf()
    print('reg')
    zeroconf.register_service(info)
    yield
    print('dereg')
    zeroconf.unregister_service(info)
    zeroconf.close()


if __name__ == '__main__':
    import time

    type_name = '_http._tcp.local.'
    desc = 'tailor test zc'
    properties = dict()
    addr = '127.0.0.1'
    port = 8080

    with zv_service_context(type_name, desc, properties, addr, port):
        time.sleep(10)
