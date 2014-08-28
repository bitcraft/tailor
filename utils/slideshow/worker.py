def thumbnailer(queue, settings):
    from pyglet.image import ImageData
    from PIL import Image, ImageOps
    import random, glob, time

    displayed = set()

    last_scan = time.time()
    files = glob.glob("{}/*jpg".format(settings['detail']))
    new = sorted(list(set(files) - displayed))

    while 1:
        if last_scan + 15 < time.time():
            last_scan = time.time()
            files = glob.glob("{}/*jpg".format(settings['detail']))
            new = sorted(list(set(files) - displayed))[15:]

        if new:
            filename = random.choice(new)
            displayed.add(filename)
        else:
            filename = random.choice(files)

        image = Image.open(filename)
        image = image.transpose(Image.FLIP_TOP_BOTTOM)
        #image.thumbnail(settings['thumbnail_size'], Image.ANTIALIAS)
        image = ImageOps.expand(image, border=12, fill=(255, 255, 255))

        w, h = image.size
        image = image.convert()
        image = ImageData(w, h, image.mode, image.tostring())
        queue.put(image)


def loader(queue, settings):
    from pyglet.image import ImageData
    from PIL import Image, ImageOps
    import random, glob, time

    displayed = set()

    last_scan = time.time()
    files = glob.glob("{}/*jpg".format(settings['originals']))
    new = sorted(list(set(files) - displayed))

    while 1:
        if last_scan + 15 < time.time():
            last_scan = time.time()
            files = glob.glob("{}/*jpg".format(settings['originals']))
            new = sorted(list(set(files) - displayed))[15:]

        if new:
            filename = random.choice(new)
            displayed.add(filename)
        else:
            filename = random.choice(files)

        image = Image.open(filename)
        image = image.transpose(Image.FLIP_TOP_BOTTOM)
        image.thumbnail(settings['large_size'], Image.ANTIALIAS)
        image = ImageOps.expand(image, border=32, fill=(255, 255, 255))

        w, h = image.size
        image = image.convert()
        image = ImageData(w, h, image.mode, image.tostring())
        queue.put(image)
