import asyncio
from tailor.plugins.composer import TemplateRenderer


class Composer:
    """
    Interface for the Tailor Workflow.  Render template graphs.
    """

    def __init__(self):
        self.incoming_image_queue = asyncio.Queue()

    @asyncio.coroutine
    def compose(self, template):
        """
        - waits for images
        - saves completed image
        """
        renderer = TemplateRenderer()
        base_image = renderer.create_blank_image(template)
        lock = asyncio.Lock()

        for node in template.placeholders_needing_image():
            node.data = yield from self.incoming_image_queue.get()
            with lock:
                renderer.render_and_paste(node, base_image)

        return base_image

    def process(self, filename):
        self.incoming_image_queue.put(filename)