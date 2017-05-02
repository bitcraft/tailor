"""
given a template and folder, make a bunch of composites
"""
import asyncio
import copy
import glob
import os.path

from PIL import Image

from tailor.builder import YamlTemplateBuilder
from tailor.plugins.composer.renderer import TemplateRenderer


def normpath(path):
    path = os.path.expanduser(path)
    path = os.path.normpath(path)
    return path


@asyncio.coroutine
def render_all_files(template, files):
    renderer = TemplateRenderer()

    filename_queue = asyncio.JoinableQueue()
    image_queue = asyncio.JoinableQueue()

    create_task = asyncio.get_event_loop().create_task

    tasks = set()
    tasks.add(create_task(async_queue_filenames(filename_queue, files)))
    tasks.add(create_task(async_consume_filenames(filename_queue, image_queue)))
    tasks.add(
        create_task(async_consume_images(template, renderer, image_queue)))
    tasks.add(filename_queue.join())

    yield from asyncio.wait(tasks)


@asyncio.coroutine
def async_consume_images(template_master, renderer, image_queue):
    index = 0

    @asyncio.coroutine
    def get():
        image = yield from image_queue.get()
        if image is None:
            raise
        return image

    while 1:
        template = copy.deepcopy(template_master)

        image0 = yield from get()
        image1 = yield from get()
        image2 = yield from get()
        image3 = yield from get()

        template.push_image(image0)
        template.push_image(image1)
        template.push_image(image2)
        template.push_image(image3)

        filename = 'composite' + str(index) + '.png'
        yield from renderer.render_all_and_save(template, filename)
        index += 1


@asyncio.coroutine
def async_consume_filenames(filename_queue, image_queue):
    create_task = asyncio.get_event_loop().create_task

    def task_done(future):
        create_task(image_queue.put(future.result()))
        filename_queue.task_done()

    while 1:
        filename = yield from filename_queue.get()
        if filename is None:
            filename_queue.task_done()
            break
        task = create_task(async_open(filename))
        task.add_done_callback(task_done)


@asyncio.coroutine
def async_queue_filenames(filename_queue, files):
    # assert(len(files) % 4 == 0)
    for index, filename in enumerate(files):
        yield from filename_queue.put(filename)
    yield from filename_queue.put(None)


@asyncio.coroutine
def async_open(filename):
    image = yield from loop.run_in_executor(None, Image.open, filename)
    return image


if __name__ == "__main__":
    import time

    start = time.time()
    loop = asyncio.get_event_loop()
    template_filename = normpath(
        'tailor/resources/templates/standard.yaml')
    template_master = YamlTemplateBuilder().read(template_filename)
    folder = normpath('~/events/carrie-jon/originals/')
    files = glob.glob('{0}/*.jpg'.format(folder))

    loop.run_until_complete(render_all_files(template_master, files))
