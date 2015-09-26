# -*- coding: utf-8 -*-
"""
Define command names and prove command/code mappings
"""
__all__ = [
    'command_lookup',
    'command_names',
]

command_names = {
    0x01: ('switch', ('pin',)),
    0x80: ('set_tilt', ('value',)),
    0x81: ('engage_relay', ('relay',)),
    0x82: ('disengage_relay', ('relay',)),
}

# Name => Code mapping for all types
command_lookup = {v[0]: k for k, v in command_names.items()}
