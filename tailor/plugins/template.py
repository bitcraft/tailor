"""
default template for INI style templates
"""
import configparser

from zope.interface import implementer

from tailor import itailor


@implementer(itailor.ITemplate)
class Template:
    def __init__(self):
        self.width = 0
        self.height = 0

    @property
    def size(self):
        return self.width, self.height

    @staticmethod
    def load(self, filename):
        template = configparser.ConfigParser()
        template.read(filename)
        self.template = template

        units = template.get('general', 'units').lower()
        if units == 'pixels':
            convert = self.convert_area_pixels
        elif units == 'inches':
            convert = self.convert_area_inches
        else:
            raise ValueError

        config = dict()
        config['units'] = units
        config['dpi'] = template.getfloat('general', 'dpi')
        config['background'] = template.get('general', 'background')
        config['width'], config['height'] = convert(
            template.get('general', 'size'))
        self.config = config

    @staticmethod
    def convert_area_pixels(self, area):
        return tuple(float(i) for i in area.split(','))

    @staticmethod
    def convert_area_inches(self, area):
        dpi = self.template.getfloat('general', 'dpi')
        return tuple(int(float(i) * dpi) for i in area.split(','))

    def layers(self):
        """ iterate over layers in draw order
        """
        template = self.template

        for section in sorted(template.sections()):
            if section.lower() == 'general':
                continue

            areas = set()
            config = dict()
            config['name'] = section
            config['areas'] = areas
            for name, value in template.items(section):
                if name.startswith('area') or name.startswith('position'):
                    areas.add(convert(value))
                else:
                    config[name] = value

            # this will return a deferred if value is not ready, and will
            # magically finish when filenames are ready
            if template.get(section, 'filename').lower() == 'auto':
                config['filename'] = yield self.filename_queue.get()


class Layer:
    implements(itailor.ILayer)

    def __init__(self):
        self.filename = None
        self.filters = None
        self.bbox = None


class LayerInstructions:
    pass
