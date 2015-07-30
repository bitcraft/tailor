import netifaces
import re


local_addr = re.compile('^(169\.254|127)')


def guess_local_ip_addresses():
    for iface in netifaces.interfaces():
        addrs = netifaces.ifaddresses(iface)
        try:
            info = addrs[netifaces.AF_INET]
        except KeyError:
            continue

        for iface in info:
            m = local_addr.match(iface['addr'])
            if m:
                continue

            return iface['addr']

