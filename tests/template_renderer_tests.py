from unittest import TestCase

from tailor.builder import JSONTemplateBuilder
from tailor.plugins.composer.renderer import TemplateRenderer


class TestRenderer(TestCase):
    def test_render(self):
        renderer = TemplateRenderer()
        builder = JSONTemplateBuilder()
        root = builder.read('../tailor/resources/templates/test_template.json')

        from PIL import Image

        im = Image.new('RGB', (1024, 1024), (128, 0, 0))
        root.push_image(im)

        im = Image.new('RGB', (1024, 1024), (0, 128, 0))
        root.push_image(im)

        im = Image.new('RGB', (1024, 1024), (0, 0, 128))
        root.push_image(im)

        im = Image.new('RGB', (1024, 1024), (255, 255, 0))
        root.push_image(im)

        image = renderer.render_all(root)
        image.save('test_image.png')
