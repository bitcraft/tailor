# -*- coding: utf-8 -*-
"""
Provide Factory class to generate and parse packet data
"""
from .commands import command_names, command_lookup


class UnhandledPacketType(Exception):
    pass


class Container(dict):
    """
    A generic container of attributes.
    Containers are the common way to express parsed data.
    """
    __slots__ = ["__keys_order__"]

    def __init__(self, **kw):
        object.__setattr__(self, "__keys_order__", [])
        for k, v in list(kw.items()):
            self[k] = v

    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            raise AttributeError(name)

    def __setitem__(self, key, val):
        if key not in self:
            self.__keys_order__.append(key)
        dict.__setitem__(self, key, val)

    def __delitem__(self, key):
        dict.__delitem__(self, key)
        self.__keys_order__.remove(key)

    __delattr__ = __delitem__
    __setattr__ = __setitem__

    def clear(self):
        dict.clear(self)
        del self.__keys_order__[:]

    def pop(self, key, *default):
        val = dict.pop(self, key, *default)
        self.__keys_order__.remove(key)
        return val

    def popitem(self):
        k, v = dict.popitem(self)
        self.__keys_order__.remove(k)
        return k, v

    def update(self, seq, **kw):

        if hasattr(seq, "keys"):
            for k in list(seq.keys()):
                self[k] = seq[k]
        else:
            for k, v in seq:
                self[k] = v
        dict.update(self, kw)

    def copy(self):
        inst = self.__class__()
        inst.update(iter(self.items()))
        return inst

    __update__ = update
    __copy__ = copy

    def __iter__(self):
        return iter(self.__keys_order__)

    iterkeys = __iter__

    def itervalues(self):
        return (self[k] for k in self.__keys_order__)

    def iteritems(self):
        return ((k, self[k]) for k in self.__keys_order__)

    def keys(self):
        return self.__keys_order__

    def values(self):
        return list(self.values())

    def items(self):
        return list(self.items())

    def __repr__(self):
        return "%s(%s)" % (self.__class__.__name__, dict.__repr__(self))


def mappp(list, dict):
    return [dict[i] for i in list]


def mapppp(values, sig):
    return {k: values[i] for i, k in enumerate(sig)}


def make_container(name, sig, values):
    return Container(name=name, **mapppp(values, sig))


# generator
def parse(handler):
    while 1:
        byte = yield

        if byte in command_names:
            name, sig = command_names[byte]
            value0 = yield
            c = make_container(name, sig, (value0,))
            handler(c)

        else:
            print(hex(byte))
            raise UnhandledPacketType


def build(name, **kwargs):
    try:
        command = command_lookup[name]
        name, sig = command_names[command]
    except KeyError:
        raise UnhandledPacketType

    if command in command_names:
        args = mappp(sig, kwargs)
        return bytearray([command, args[0]])

    else:
        raise Exception
