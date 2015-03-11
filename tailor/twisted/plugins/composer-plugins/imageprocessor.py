import sys

sys.path.append('/home/mjolnir/git/tailor')

import os


def autocrop(image, area):
    x, y, w, h = area
    r0 = float(w) / h
    r1 = float(image.width) / image.height

    if r1 > r0:
        scale = float(h) / image.height
        sw = int(image.width * scale)
        cx = int((sw - w) / 2)
        image.resize(sw, h)
        image.crop(left=cx, top=0,
                   right=image.width - cx, bottom=image.height)

    return image


def scale(image, area):
    x, y, w, h = area
    image.resize(w, h)
    return image


def toaster(image, area):
    x, y, w, h = area
    scratch = 'prefilter-{}.miff'.format(image_config['filename'])
    image.filename = image_config['filename']
    image.format = os.path.splitext(scratch)[1][1:]
    image.save(filename=scratch)
    image.close()
    scratch = toaster(scratch, sw, h)
    return scratch


filters = {
    'autocrop': autocrop,
    'scale': scale,
    'toaster': toaster,
}


def image_processor(task_queue, finished_queue, global_config):
    """
    image processing worker
    this will take one section of a template ("00portrait", etc)
    """
    # hack to get around stale references
    from wand.image import Image

    units = global_config['units']
    dpi = global_config['dpi']

    # get an image from the queue
    config = task_queue.get()

    image = Image(filename=config['filename'])
    sizes = set()

    # the 'area' key in template configs defines where an image is positioned
    # on the final product.  it can be listed more than once, and it is
    # checked here.  each area key can be filtered, cropped, and is scaled
    # to fit into each area/

    for area in (i for i in config.keys() if i[:4].lower() == 'area'):
        area = tuple(float(i) for i in config['area'].split(','))

        if units == 'pixels':
            x, y, w, h = (int(i) for i in area)

        elif units == 'inches':
            x, y, w, h = (int(i * dpi) for i in area)

        # prevent processing an image if it has already been processed at
        # the same size, but with a different position
        if (w, h) in sizes:
            continue
        sizes.add((w, h))

        # create a new image in memory for manipulation with Wand
        scratch = "scratch.tmp"
        with Image(filename=scratch) as temp_image:
            image = Image(image=temp_image)
        del temp_image

        # bug: filters will be out of order, resulting in unpredictable results
        for key in config.keys():
            try:
                filters[key](image, (x, y, w, h))
            except KeyError:
                pass

        this_config = dict(config)
        this_config['area'] = (x, y, w, h)
        ready_queue.put(this_config)

    # the position keyword can be used if the target file is just positioned,
    # but not scaled.

    for pos in (i for i in config.keys() if i[:8].lower() == 'position'):
        pos = image_config[pos]

        if units == 'pixels':
            x, y = (int(i) for i in pos.split(','))
            w, h = image.size
        elif units == 'inches':
            x, y = (int(i * dpi) for i in pos.split(','))
            w, h = (int(i / dpi) for i in image.size)

        this_config = dict(config)
        this_config['area'] = (x, y, w, h)
        ready_queue.put(this_config)

