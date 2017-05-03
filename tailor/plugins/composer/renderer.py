# -*- coding: utf-8 -*-
"""
utilities for templates

needs asyncio audit
"""
import asyncio

from PIL import Image

from .filters.autocrop import Autocrop

__all__ = ('TemplateRenderer', )


class TemplateRenderer:
    """
    Render template graphs using PIL
    """
    image_mode = 'RGBA'

    def __init__(self):
        self.handlers = {
            'area': self.render_area_node,
            'image': self.render_image_node,
            'placeholder': self.render_cropped_node
        }

    def render_node(self, node):
        """ Render one node
        
        :param node: TemplateNode
        :return: (PIL Image or None, Rect or None)
        """
        try:
            func = self.handlers[node.kind]
        except KeyError:
            return None, None
        return func(node)

    def render_all(self, root):
        """ Render a new image and all nodes.  Must pass in the root node.

        :param root: Root node
        """
        def func():
            base_image = self.create_blank_image(root)

            for node in root.bfs_children():
                self.render_and_paste(node, base_image)

            return base_image

        loop = asyncio.get_event_loop()
        return loop.run_in_executor(None, func)

    @asyncio.coroutine
    def render_all_and_save(self, root, filename):
        """ Render the template, then save it to a file
        
        :param root: 
        :param filename:
         
        :type root:
        :type filename: str

        :returns: None
        """
        image = yield from self.render_all(root)
        loop = asyncio.get_event_loop()
        return loop.run_in_executor(None, image.save, filename)

    def render_and_paste(self, node, base_image):
        """ Render a node, if there is a result, then paste to the base_image

        :param node: TemplateNode
        :param base_image: PIL image

        :return: PIL Image of node, else None
        """
        image, rect = self.render_node(node)
        if image is not None:
            x, y, w, h = rect
            self.paste(image, base_image, (x, y))

        return image

    @staticmethod
    def paste(upper, lower, top_left):
        # correctly handle the alpha channel transparency.
        if upper.mode == 'RGBA':
            lower.paste(upper, top_left, mask=upper)
        else:
            lower.paste(upper, top_left)

    def render_area_node(self, node):
        # draw = ImageDraw.Draw(self.image)
        # draw.rectangle(rect, (0, 255, 255))
        return None, None

    def render_image_node(self, node):
        # LIMITATIONS: only pastes to area, no scaling
        try:
            if node.filename is not None:
                node.data = Image.open(node.filename)
        except FileNotFoundError:
            node.data = None

        # TODO: scaling options, ect, processing chain
        if node.data is not None:
            root = node.get_root()
            area = self.convert_rect(node.parent.rect, root.dpi)
            return node.data, area

        return None, None

    def render_cropped_node(self, node):
        if node.data:
            root = node.get_root()
            # TODO: move these functions into a processing chain
            area = self.convert_rect(node.parent.rect, root.dpi)
            image = Autocrop().process(node.data, area)
            print(area)
            return image, area
        # TODO: lazy loading of images
        return None, None

    def create_blank_image(self, node):
        root = node.get_root()
        size = root.determine_rect()[2:]
        pixel_size = self.convert_from_image_to_pixel(size, root.dpi)
        return Image.new(self.image_mode, pixel_size)

    def convert_rect(self, rect, dpi):
        x1, y1, w, h = self.convert_from_image_to_pixel(rect, dpi)
        x1, y1, x2, y2 = self.convert_from_xywh((x1, y1, w, h))
        return x1, y1, w, h

    @staticmethod
    def convert_from_image_to_pixel(area, dpi):
        return [int(i * dpi) for i in area]

    @staticmethod
    def convert_from_xywh(rect):
        x, y, w, h = rect
        return x, y, x + w, y + h
