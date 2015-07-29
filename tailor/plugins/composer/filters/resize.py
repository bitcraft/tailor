from PIL import Image

from tailor.plugins.composer import ComposerFilter


class Scale(ComposerFilter):
    resize_filter = Image.LANCZOS

    def process(self, image, area):
        w, h = area[2:]
        image.resize(w, h)
        return image
