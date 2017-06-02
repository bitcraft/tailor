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


def double(image, filename):
    base = Image.new('RGBA', (1200, 1800))
    areas = ((0, 0), (600, 0))
    for area in areas:
        base.paste(image, area, mask=image)
    base.save(filename)


def normpath(path):
    path = os.path.expanduser(path)
    path = os.path.normpath(path)
    return path


async def render_all_files(template, files):
    renderer = TemplateRenderer()

    filename_queue = asyncio.Queue()
    image_queue = asyncio.Queue()

    create_task = asyncio.get_event_loop().create_task

    tasks = set()
    tasks.add(create_task(async_queue_filenames(filename_queue, files)))
    tasks.add(create_task(async_consume_filenames(filename_queue, image_queue)))
    tasks.add(create_task(async_consume_images(template, renderer, image_queue)))
    tasks.add(filename_queue.join())

    await asyncio.wait(tasks)


async def async_consume_images(template_master, renderer, image_queue):
    index = 0

    async def get():
        image = await image_queue.get()
        if image is None:
            raise ValueError
        return image



    while 1:
        template = copy.deepcopy(template_master)

        image0 = await get()
        image1 = await get()
        image2 = await get()
        image3 = await get()

        template.push_image(image0)
        template.push_image(image1)
        template.push_image(image2)
        template.push_image(image3)

        filename = 'session-melissa-robbie-{:05d}.jpg'.format(index)
        image = await renderer.render_all(template)
        double(image, filename)
        print(filename)
        index += 1


async def async_consume_filenames(filename_queue, image_queue):
    create_task = asyncio.get_event_loop().create_task

    def task_done(future):
        create_task(image_queue.put(future.result()))
        filename_queue.task_done()

    while 1:
        filename = await filename_queue.get()
        if filename is None:
            filename_queue.task_done()
            break
        task = create_task(async_open(filename))
        task.add_done_callback(task_done)


async def async_queue_filenames(filename_queue, files):
    assert (len(files) % 4 == 0)
    for index, filename in enumerate(sorted(files)):
        await filename_queue.put(filename)
    await filename_queue.put(None)


async def async_open(filename):
    image = await loop.run_in_executor(None, Image.open, filename)
    return image


async def main():
    template_filename = normpath('tailor/resources/templates/standard.yaml')
    template_master = YamlTemplateBuilder().read(template_filename)
    folder = normpath(os.path.join("z:", "Dropbox", "photob", "erin-drew"))
    files = glob.glob('{0}/*.jpg'.format(folder))
    assert files
    files.sort()

    renderer = TemplateRenderer()

    index = 0
    while files:
        template = copy.deepcopy(template_master)

        image0 = Image.open((files.pop(0)))
        image1 = Image.open((files.pop(0)))
        image2 = Image.open((files.pop(0)))
        image3 = Image.open((files.pop(0)))

        template.push_image(image0)
        template.push_image(image1)
        template.push_image(image2)
        template.push_image(image3)

        filename = 'session-erin-drew-{:05d}.jpg'.format(index)
        image = await renderer.render_all(template)
        double(image, filename)
        print(filename)
        index += 1

        print(files)


if __name__ == "__main__":
    import time

    import asyncio
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
