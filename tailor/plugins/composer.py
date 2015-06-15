"""
image processor/composer that manipulates images
"""
import asyncio

from PIL import Image

from zope.interface import implementer
from tailor import itailor


def composite(base, layers):
    """
    layer a bunch of images, taking into consideration transparency
    """
    for config, images in layers:
        for area, image in images:
            if image.mode == 'RGBA':
                base.paste(image, area[:2], mask=image)
            else:
                base.paste(image, area[:2])


@implementer(itailor.IFileOp)
class Composer:
    """
    uses templates and images to create print layouts
    """

    def __init__(self, template):
        self.template = template
        self.filename_queue = asyncio.Queue()

    def process_area(config):
        """
        image processing worker
        """
        # create a new image in memory for manipulation with pillow
        master = Image.open(config['filename'])

        # the 'area' key in template configs defines where an image is positioned
        # on the final product.  it can be listed more than once, and it is
        # checked here.  each area key can be filtered, cropped, and is scaled
        # to fit into each area.
        cache = dict()

        def paint(area):
            x, y, w, h = area

            try:
                image = cache[(w, h)]
            except KeyError:
                # bug: filters will be out of order
                image = master.copy()

                for key in list(config.keys()):
                    try:
                        image = filters[key](image, (x, y, w, h))
                    except KeyError:
                        pass

                image.load()  # required by PIL to commit modifications
                cache[(w, h)] = image
            return area, image

        images = [paint(area) for area in config['areas']]
        return config, images

    @asyncio.coroutine
    def compose(self):
        """
        waits for filenames
        filters/resizes each file
        """
        template = self.template

        # TODO: JoinableQueue is depreciated, change to Queue
        queue = asyncio.JoinableQueue()

        for area in template.areas():
            if area.source == 'auto':
                filename = yield from self.filename_queue.get()
            self.process_area(area)

        queue.join()
        base = Image.new("RGBA", template.size)
        filename = 'composite.png'
        composite(base, layers)
        base.save(filename)

    def process(self, filename):
        self.filename_queue.put(filename)
