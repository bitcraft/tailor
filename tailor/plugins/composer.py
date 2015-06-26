"""
image processor/composer that manipulates images
"""
import asyncio

from tailor.template import TemplateRenderer


class Composer:
    """
    uses templates and images to create print layouts
    """

    def __init__(self, template):
        self.template = template
        self.incoming_image_queue = asyncio.Queue()

    @asyncio.coroutine
    def compose(self):
        """
        waits for images
        filters/resizes each image

        TODO: allow incremental rendering, instead of all at once
        """
        # TODO: JoinableQueue is depreciated, change to Queue
        queue = asyncio.JoinableQueue()

        for node in self.template.placeholders_needing_image():
            node.data = yield from self.incoming_image_queue.get()

        queue.join()
        renderer = TemplateRenderer()
        image = renderer.render(self.template)
        filename = 'composite.png'
        image.save(filename)

    def process(self, filename):
        self.incoming_image_queue.put(filename)
