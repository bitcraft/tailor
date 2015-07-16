from tailor.plugins.composer import ComposerFilter
from PIL import Image


class Scale(ComposerFilter):
    resize_filter = Image.LANCZOS

    def process(self, image, area):
        w, h = area[2:]
        image.resize(w, h)
        return image
