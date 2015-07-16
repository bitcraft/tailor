from PIL import Image


class Autocrop:
    def process(self, image, area):
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
