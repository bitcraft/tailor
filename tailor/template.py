"""
utilities for templates
"""
import json

from .graph import Node


__all__ = ('JSONTemplateBuilder',
           'AreaNode',
           'ImageNode',
           'ImagePlaceholderNode',
           'TemplateRenderer')

def is_number(value):
    """Test if an object is a number.
    :param value: some object
    :return: True
    :raises: ValueError
    """
    try:
        float(value)
    except (ValueError, TypeError):
        raise ValueError

    return True


class AreaNode(Node):
    """ area
    """
    accepts = {'AreaNode', 'ImageNode', 'ImagePlaceholderNode'}

    def __init__(self, rect, units, dpi, name=None):
        super().__init__()
        self.rect = rect
        self.units = units
        self.dpi = dpi
        self.name = name

    def needed_captures(self):
        """Search and return number of images needed

        :param node:
        :type node:
        :return:
        :rtype:
        """
        needed = 0
        for child in self.dfs_children():
            if isinstance(child, ImagePlaceholderNode):
                if child.data is None:
                    needed += 1
        return needed

    def push_image(self, data):
        print(list(self.dfs_children()))
        for child in self.dfs_children():
            if isinstance(child, ImagePlaceholderNode):
                if child.data is None:
                    child.data = data
                    return

        print('missed')

class ImageNode(Node):
    """
    represents an image
    """
    # does not accept other nodes

    def __init__(self, data, name=None):
        super().__init__()
        self.data = data
        self.name = name


class ImagePlaceholderNode(Node):
    """
    accepts images from a push
    """
    accepts = (ImageNode, )

    def __init__(self, data, name=None):
        super().__init__()
        self.data = data
        self.name = name


class JSONTemplateBuilder:
    valid_units = ('inches', )

    class SyntaxError(Exception):
        pass

    def __init__(self):
        self.handlers = {
            'area': (self.handle_area_node, AreaNode),
            'image': (self.handle_image_node, ImageNode),
            'placeholder': (self.handle_image_node, ImagePlaceholderNode)
        }

    def read(self, filename):
        with open(filename) as fp:
            root = self.build_root_node(json.load(fp))
        return root

    def build_root_node(self, json_graph):
        root = self.build_node(json_graph)
        if not self.verify_root_node(root):
            raise JSONTemplateBuilder.SyntaxError

        self.build_graph(root, json_graph)

        return root

    def build_graph(self, root, json_graph):
        try:
            children = json_graph['children']
        except KeyError:
            return

        for child_graph in children:
            child = self.build_node(child_graph)
            if child.__class__.__name__ not in root.accepts:
                raise JSONTemplateBuilder.SyntaxError

            root.add_child(child)
            self.build_graph(child, child_graph)

    def build_node(self, json_graph):
        try:
            node_type = json_graph['type']
        except KeyError:
            raise JSONTemplateBuilder.SyntaxError

        try:
            parser, node_class = self.handlers[node_type]
        except KeyError:
            raise ValueError

        return self.node_builder(parser, node_class, json_graph)

    @staticmethod
    def node_builder(parser, node_class, json_graph):
        try:
            data = json_graph['data']
        except KeyError:
            raise JSONTemplateBuilder.SyntaxError
        args = parser(data)
        name = json_graph.get('name', None)
        return node_class(*args, name=name)

    def handle_area_node(self, data):
        rect = self.cast_list_float(data['rect'])
        units = data.get('units', None)
        try:
            dpi = float(data['dpi'])
        except KeyError:
            dpi = None
        return rect, units, dpi

    def handle_image_node(self, data):
        filename = data.get('filename', None)
        return filename,  # the comma is not a mistake...leave it

    @staticmethod
    def cast_list_float(values):
        """

        :param node:
        :return:
        :raises: syntaxerror
        """
        # rect values must be a number
        try:
            return [float(i) for i in values]
        except (ValueError, TypeError):
            raise JSONTemplateBuilder.SyntaxError

    @staticmethod
    def verify_root_node(node):
        """ root node: must be area and called root
                       must have dpi and units
                       area must start with 0, 0

        :rtype: bool
        """
        if not isinstance(node, AreaNode):
            return False

        if not node.name == 'root':
            return False

        if node.dpi is None or node.units is None:
            return False

        if not node.rect[:2] == [0, 0]:
            return False

        return True


from PIL import Image

# 1.55 width
# 1.27 height

class TemplateRenderer:
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
            print(child.__class__.__name__)
            self.handle_node(child)
            self.image.save('step' + str(i) + '.png')

        self.image.save('image.png')

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

    def convert_from_xywh(self, rect):
        x, y, w, h = rect
        return x, y, x + w, y + h
