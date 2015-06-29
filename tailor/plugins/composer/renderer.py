"""
utilities for templates
"""
from PIL import Image

from tailor.graph import AreaNode, ImageNode, ImagePlaceholderNode

__all__ = ('TemplateRenderer',)


class TemplateRenderer:
    """
    Render template graphs using PIL
    """
    mode = 'RGBA'

    def __init__(self):
        self.renderers = {
            AreaNode: self.render_area_node,
            ImageNode: self.render_image_node,
            ImagePlaceholderNode: self.render_image_node
        }

    def render_node(self, node):
        """ Render one node
        :param node: TemplateNode
        :return: (PIL Image or None, Rect or None)
        """
        try:
            func = self.renderers[node.__class__]
        except KeyError:
            return
        return func(node)

    def render_all(self, root):
        """ Render a new image and all nodes.  Must pass in the root node.

        :param root: Root node
        :return: PIL Image
        """
        base_image = self.create_blank_image(root)

        for i, node in enumerate(root.bfs_children()):
            self.render_and_paste(node, base_image)

        return base_image

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
        if node.data:
            root = node.get_root()
            return node.data, self.convert_rect(node.parent.rect, root.dpi)
        return None, None

    def create_blank_image(self, node):
        root = node.get_root()
        size = root.determine_rect()[2:]
        pixel_size = self.convert_from_image_to_pixel(size, root.dpi)
        return Image.new(self.mode, pixel_size)

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
