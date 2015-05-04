from zope.interface import implementer
from PIL import Image

from tailor import itailor


@implementer(itailor.IImageOp)
class Autocrop:
    @staticmethod
    def process(image, area):
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


class Scale:
    implements(itailor.IImageOp)

    @staticmethod
    def process(image, area):
        x, y, w, h = area
        image.resize(w, h)
        return image
