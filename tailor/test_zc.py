import socket
import json
from time import sleep

from zeroconf import ServiceBrowser, ServiceStateChange, Zeroconf


def on_service_state_change(zeroconf, service_type, name, state_change):
    print("Service %s of type %s state changed: %s" % (name, service_type, state_change))

    if state_change is ServiceStateChange.Added:
        info = zeroconf.get_service_info(service_type, name)
        if info:
            print("  Address: %s:%d" % (socket.inet_ntoa(info.address), info.port))
            print("  Weight: %d, priority: %d" % (info.weight, info.priority))
            print("  Server: %s" % (info.server,))
            if info.properties:
                print("  Properties are:")
                for key, value in info.properties.items():
                    print("    %s: %s" % (key, value))
            else:
                print("  No properties")
        else:
            print("  No info")
        print('\n')

if __name__ == '__main__':
    # TODO: move to more generic loader
    filename = 'config/kiosk.json'
    with open(filename) as fp:
        json_data = json.load(fp)

    listeners = json_data['zeroconf-listeners']
    listener = listeners.pop()

    config = listener['config']
    service_type = config['type']
    print(service_type)

    print("\nBrowsing services, press Ctrl-C to exit...\n")

    zeroconf = Zeroconf()
    browser = ServiceBrowser(zeroconf, service_type, handlers=[on_service_state_change])

    try:
        while True:
            sleep(0.1)
    except KeyboardInterrupt:
        pass
    finally:
        zeroconf.close()
