# -*- coding: utf-8 -*-
from PIL import Image, ImageOps


class Autocrop:
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
        return ImageOps.fit(
            image, (int(w), int(h)), Image.ANTIALIAS
        )

        iw, ih = image.size

        r0 = float(w) / h
        r1 = float(iw) / ih

        # wide images
        if r0 > r1:
            scale = float(h) / ih
            sw = int(iw * scale)
            cx = int((sw - w) / 2)
            image = image.resize((sw, h), Image.ANTIALIAS)
            iw, ih = image.size
            image = image.crop((cx, 0, iw - cx, ih))

        # tall images
        # TODO: this.
        elif r0 > r1:
            print('unhandled image size')

            pass
            # scale = float(w) / iw
            # sh = int(ih * scale)
            # cx = int((sw - w) / 2)
            # image = image.resize((sw, h), Image.ANTIALIAS)
            # iw, ih = image.size
            # image = image.crop((cx, 0, iw - cx, ih))

        # square images
        else:
            print('its hip to be square')
            image = image.resize((w, h), Image.ANTIALIAS)

        return image
