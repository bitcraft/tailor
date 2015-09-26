# -*- coding: utf-8 -*-
import netifaces
import re

local_addr = re.compile('^(169\.254|127)')


def ip_interfaces():
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
    for iface in ip_interfaces():
        addr = iface['addr']
        if guess_routable(addr):
            return addr


def guess_unroutable_addresses():
    for iface in ip_interfaces():
        addr = iface['addr']
        if not guess_routable(addr):
            return addr
