from PIL import Image


class ImageThumb:
    """
    simple thumbnailer.

    spawns a thread that resizes the image.
    creates a square crop to the size passed
    """

    def __init__(self, size, destination):
        self.size = size
        self.destination = destination

    def process(self, filename):
        image = Image.open(filename)
        image.thumbnail(self.size)
        image.save(self.destination)
        return self.destination
