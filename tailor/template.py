"""
utilities for templates
"""


def needed_captures(template):
    captures = 0
    for section in template.sections():
        try:
            if template.get(section, 'filename').lower() == 'auto':
                captures += 1
        except:
            pass
    return captures
