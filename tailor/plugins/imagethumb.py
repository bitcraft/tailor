from PIL import Image
import asyncio


class ImageThumb:
    """
    simple thumbnailer.

    spawns a thread that resizes the image.
    creates a square crop to the size passed
    """
    def __init__(self, size, destination):
        self.size = size
        self.destination = destination

    def process(self, *args):
        def func():
            image = Image.open(filename)
            image.thumbnail(self.size)
            image.save(self.destination)

        loop = asyncio.get_event_loop()
        loop.run_in_executor(None, func, args)
        return self.destination
