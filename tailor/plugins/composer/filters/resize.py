from tailor.plugins.composer import ComposerFilter
from PIL import Image


class Scale(ComposerFilter):
    resize_filter = Image.LANCZOS

    def process(self, image, area):
        x, y, w, h = area
        image.resize(w, h)
        return image
