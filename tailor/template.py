"""
utilities for templates
"""
from abc import ABCMeta, abstractmethod

from PIL import Image

from tailor.graph import AreaNode, ImageNode, ImagePlaceholderNode

__all__ = ('TemplateRenderer',)


class NodeRenderer(metaclass=ABCMeta):
    @abstractmethod
    def render(self, node):
        pass


class AreaNodeRenderer(NodeRenderer):
    def render(self, node):
        pass


class TemplateRenderer:
    """
    Render template graphs using PIL
    """
    mode = 'RGBA'
    resize_filter = Image.LANCZOS

    def __init__(self):
        self.handlers = {
            AreaNode: self.handle_area_node,
            ImageNode: self.handle_image_node,
            ImagePlaceholderNode: self.handle_image_node
        }
        self.dpi = None
        self.units = None
        self.image = None

    def render(self, node):
        self.dpi = node.dpi
        self.units = node.units

        self.image = self.create_blank_image(node)
        for i, child in enumerate(node.bfs_children()):
            self.handle_node(child)
            # self.image.save('step' + str(i) + '.png')

        return self.image

    def handle_node(self, node):
        try:
            handler = self.handlers[node.__class__]
        except KeyError:
            return

        handler(node)

    def handle_area_node(self, node):
        pass

    def handle_image_node(self, node):
        # draw = ImageDraw.Draw(self.image)
        # draw.rectangle(rect, (0, 255, 255))
        if node.data:
            x1, y1, w, h = self.convert_from_image_to_pixel(node.parent.rect)
            x1, y1, x2, y2 = self.convert_from_xywh((x1, y1, w, h))
            im = self.resize_image(node.data, (w, h))

            # correctly handle the alpha channel transparency.
            if im.mode == 'RGBA':
                self.image.paste(im, (x1, y1), mask=im)
            else:
                self.image.paste(im, (x1, y1))

    def resize_image(self, source, size):
        """
        :param source: PIL image
        :param size: (w, h)
        :return: new PIL image
        """
        im = source.resize(size, self.resize_filter)
        return im

    def create_blank_image(self, node):
        size = node.rect[2:]
        pixel_size = self.convert_from_image_to_pixel(size)
        return Image.new(self.mode, pixel_size)

    def convert_from_image_to_pixel(self, area):
        return [int(i * self.dpi) for i in area]

    @staticmethod
    def convert_from_xywh(rect):
        x, y, w, h = rect
        return x, y, x + w, y + h
