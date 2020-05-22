# -*- coding: utf-8 -*-
import sys
from unittest import TestCase

sys.path.extend(['..', '.'])

from tailor.builder import YamlTemplateBuilder
from tailor.plugins.composer.renderer import TemplateRenderer


async def test_render():
    renderer = TemplateRenderer()
    builder = YamlTemplateBuilder()
    root = builder.read('tailor/resources/templates/standard.yaml')

    from PIL import Image

    im = Image.new('RGB', (5184, 3456), (128, 0, 0))
    root.push_image(im)

    im = Image.new('RGB', (1024, 1024), (0, 128, 0))
    root.push_image(im)

    im = Image.new('RGB', (1024, 1024), (0, 0, 128))
    root.push_image(im)

    im = Image.new('RGB', (1024, 1024), (255, 255, 0))
    root.push_image(im)

    await renderer.render_all_and_save(root, 'test_image.png')


if __name__ == '__main__':
    import asyncio

    loop = asyncio.get_event_loop()
    loop.run_until_complete(test_render())
    print('done')


class TestRenderer(TestCase):
    def test_render(self):
        test_render()
