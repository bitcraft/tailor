# -*- coding: utf-8 -*-
import logging
import re

logger = logging.getLogger("tailor.net")
try:
    import netifaces
except ImportError:
    logger.critical("cannot import netifances.  some network services disabled.")
    netifaces = None

local_addr = re.compile(r"^(169\.254|127)")


def ip_interfaces():
    if netifaces is None:
        return ["127.0.0.1"]

    for iface in netifaces.interfaces():
        ifadresses = netifaces.ifaddresses(iface)
        try:
            ip4 = ifadresses[netifaces.AF_INET]
        except KeyError:
            continue
        for addr_info in ip4:
            yield addr_info


def guess_routable(addr):
    return bool(local_addr.match(addr))


def guess_local_ip_addresses():
    if netifaces is None:
        return "127.0.0.1"

    for iface in ip_interfaces():
        addr = iface["addr"]
        if guess_routable(addr):
            return addr


def guess_unroutable_addresses():
    for iface in ip_interfaces():
        addr = iface["addr"]
        if not guess_routable(addr):
            return addr
