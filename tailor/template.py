"""
utilities for templates
"""
import json

from .graph import Node


__all__ = ('JSONTemplateBuilder',
           'AreaNode',
           'ImageNode')

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
    accepts = {'AreaNode', 'ImageNode'}

    def __init__(self, area, units, dpi, name=None):
        super().__init__()
        self.area = area
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
            if isinstance(child, ImageNode):
                if child.data is None:
                    needed += 1
        return needed


class ImageNode(Node):
    """
    represents an image
    """
    # does not accept other nodes

    def __init__(self, data, name=None):
        super().__init__()
        self.data = data
        self.name = name


class JSONTemplateBuilder:
    valid_units = ('inches', )

    class SyntaxError(Exception):
        pass

    def __init__(self):
        self.node_parsers = {
            'area': (self.parse_area_node, AreaNode),
            'image': (self.parse_image_node, ImageNode)
        }

    def read(self, filename):
        with open(filename) as fp:
            self.build_root_node(json.load(fp))

    def build_root_node(self, json_graph):
        root = self.build_node(json_graph)
        if not self.verify_root_node(root):
            raise JSONTemplateBuilder.SyntaxError

        for child_graph in json_graph['children']:
            child = self.build_node(child_graph)
            root.push(child)

        return root

    def build_node(self, json_graph):
        try:
            node_type = json_graph['type']
            data = json_graph['data']
        except KeyError:
            raise JSONTemplateBuilder.SyntaxError

        try:
            parser, node_class = self.node_parsers[node_type]
        except KeyError:
            raise ValueError

        return self.node_builder(parser, node_class, json_graph)

    @staticmethod
    def node_builder(parser, node_class, json_graph):
        name = json_graph.get('name', None)
        args = parser(json_graph['data'])
        return node_class(*args, name=name)

    def parse_area_node(self, data):
        rect = self.cast_list_float(data['rect'])
        units = data.get('units', None)
        try:
            dpi = float(data['dpi'])
        except KeyError:
            dpi = None
        return rect, units, dpi

    def parse_image_node(self, data):
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

        :rtype: bool
        """
        if not isinstance(node, AreaNode):
            return False

        if not node.name == 'root':
            return False

        if node.dpi is None or node.units is None:
            return False

        return True

