# -*- coding: utf-8 -*-
from PIL import Image, ImageOps


class Autocrop:
    """ Crop is correctly centered.  No need to adjust or test.

    """
    def process(self, image, area):
        # x1 = y1 = 0
        # x2, y2 = image.size
        # wRatio = 1.0 * x2 / area[0]
        # hRatio = 1.0 * y2 / area[1]
        # if hRatio > wRatio:
        #     y1 = int(y2 / 2 - area[1] * wRatio / 2)
        #     y2 = int(y2 / 2 + area[1] * wRatio / 2)
        # else:
        #     x1 = int(x2 / 2 - area[0] * hRatio / 2)
        #     x2 = int(x2 / 2 + area[0] * hRatio / 2)
        # image = image.crop((x1, y1, x2, y2))
        x, y, w, h = area
        return ImageOps.fit(image, (int(w), int(h)), Image.ANTIALIAS)
