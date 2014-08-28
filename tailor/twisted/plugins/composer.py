from twisted.plugin import IPlugin
from twisted.internet import defer
from twisted.internet import threads

from zope.interface import implements
from tailor import itailor
from PIL import Image


"""
image processor/composer that manipulates images
in memory according to an ini-styles template system

how things generally work:
    the composer reads a template
    generate a new config for each image in the template
    using a pool of workers that process each image
    when workers are finshed, layer images for final output
"""

# ===========================================================
# Image manipulation functions
#
def autocrop(image, area):
    iw, ih = image.size
    x, y, w, h = area
    r0 = float(w) / h
    r1 = float(iw) / ih

    if r1 > r0:
        scale = float(h) / ih
        sw = int(iw * scale)
        cx = int((sw - w) / 2)
        image = image.resize((sw, h), Image.BICUBIC)
        iw, ih = image.size
        image = image.crop((cx, 0, iw - cx, ih))

    return image


def scale(image, area):
    x, y, w, h = area
    image.resize(w, h)
    return image


filters = {
    'autocrop': autocrop,
    'scale': scale,
}
# ===========================================================


def composite(config, layers, filename):
    """
    layer a bunch of images.  not in the Composer object since
    this is meant to run in another thread
    """
    base = Image.new("RGBA", (config['width'], config['height']),
                     config['background'])

    for config, images in layers:
        for area, image in images:
            if image.mode == 'RGBA':
                base.paste(image, area[:2], mask=image)
            else:
                base.paste(image, area[:2])
    base.save(filename)
    return filename


def image_processor(config):
    """
    image processing worker
    this will take one section of a template ("00portrait", etc)
    """
    # create a new image in memory for manipulation with Wand
    master = Image.open(config['filename'])

    # the 'area' key in template configs defines where an image is positioned
    # on the final product.  it can be listed more than once, and it is
    # checked here.  each area key can be filtered, cropped, and is scaled
    # to fit into each area/
    cache = dict()

    def func(area):
        if len(area) == 4:
            x, y, w, h = area
        elif len(area) == 2:
            x, y = area
            w, h = master.size

        try:
            image = cache[(w, h)]
        except KeyError:
            # bug: filters will be out of order, resulting in unpredictable results
            image = master.copy()

            for key in config.keys():
                try:
                    image = filters[key](image, (x, y, w, h))
                except KeyError:
                    pass

            image.load()  # required by PIL to commit modifications
            cache[(w, h)] = image
        return area, image

    images = [func(area) for area in config['areas']]
    return config, images


class Composer(object):
    """
    uses templates and images to create print layouts
    """
    implements(itailor.IFileOp)

    def __init__(self, template, **kwargs):
        self.template = template
        self.ready_queue = defer.DeferredQueue()
        self.filename_queue = defer.DeferredQueue()
        self.running = False

    @defer.inlineCallbacks
    def compose(self):
        """
        waits for filenames
        makes one thread for each file
        filters/resizes each file
        when all are ready, call the compose() thread
        """
        template = self.template

        units = template.get('general', 'units').lower()
        if units == 'pixels':
            convert = self.convert_area_pixels
        elif units == 'inches':
            convert = self.convert_area_inches

        # generate a config that is sent to the workers
        # it reamins a python dict so it may be easily serialized
        config = dict()
        config['units'] = units
        config['dpi'] = template.getfloat('general', 'dpi')
        config['background'] = template.get('general', 'background')
        config['width'], config['height'] = convert(
            template.get('general', 'size'))
        self.config = config

        _threads = []
        # sections are made for the worker threads
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

            # get our processing thread going
            _threads.append(threads.deferToThread(image_processor, config))

        # this will wait until all threads have finished
        t = yield defer.DeferredList(_threads)
        layers = []
        for result, values in t:
            if not result:
                raise ValueError
            config, images = values
            layers.append((config, images))

        # layers are sorted with the last items 'on top' of the final image
        layers.sort(key=lambda i: i[0]['name'])

        filename = 'composite.png'
        yield threads.deferToThread(composite, self.config, layers, filename)

        defer.returnValue(filename)

    def convert_area_pixels(self, area):
        return tuple(float(i) for i in area.split(','))

    def convert_area_inches(self, area):
        dpi = self.template.getfloat('general', 'dpi')
        return tuple(int(float(i) * dpi) for i in area.split(','))

    def process(self, filename):
        self.filename_queue.put(filename)
        if self.running:
            return None
        else:
            self.running = True
            return self.compose()


class ComposerFactory(object):
    implements(IPlugin, itailor.iTailorPlugin)
    __plugin__ = Composer

    @classmethod
    def new(cls, *args, **kwargs):
        return cls.__plugin__(*args, **kwargs)


factory = ComposerFactory()
