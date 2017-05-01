# -*- coding: utf-8 -*-
"""
Render a template so that is can be used as a mask layer
or guid when using editors such as Gimp, Pixelmator, or
Photoshop to create template images.
"""
import asyncio

from tailor.builder import JSONTemplateBuilder
from tailor.plugins.composer.renderer import TemplateRenderer


async def test_render():
    renderer = TemplateRenderer()
    builder = JSONTemplateBuilder()
    root = builder.read('tailor/resources/templates/test_template.json')

    from PIL import Image

    im = Image.new('RGB', (5184, 3456), (128, 0, 0))
    root.push_image(im)

    im = Image.new('RGB', (1024, 1024), (0, 128, 0))
    root.push_image(im)

    im = Image.new('RGB', (1024, 1024), (0, 0, 128))
    root.push_image(im)

    im = Image.new('RGB', (1024, 1024), (255, 255, 0))
    root.push_image(im)

    image = renderer.render_all(root)


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(test_render())
    print('done')
