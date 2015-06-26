""" Support loading template graphs from json formatted files
"""
import json
from abc import ABCMeta, abstractmethod

from tailor.graph import AreaNode, ImageNode, ImagePlaceholderNode

__all__ = ['cast_list_float',
           'AreaNodeHandlerHandler',
           'ImageNodeHandlerHandler',
           'ImagePlaceholderNodeHandlerHandler',
           'RootNodeHandler',
           'TemplateBuilder',
           'JSONTemplateBuilder']


def cast_list_float(values):
    """

    :param values: list of stuff
    :return: list of stuff as floats
    :raises: ValueError TypeError
    """
    # rect values must be a number
    try:
        return [float(i) for i in values]
    except (ValueError, TypeError):
        raise TemplateBuilder.SyntaxError


class TemplateNodeHandler(metaclass=ABCMeta):
    @abstractmethod
    def parse_init_args(self, node):
        """Given a dictionary of data, return a tuple suitable
           for creating an instance of a class for this handler

           raise syntax errors if needed
        """
        raise NotImplementedError

    def create_node(self, data_dict):
        args = self.parse_init_args(data_dict)
        name = data_dict.get('name', None)
        try:
            node = self.node(*args, name=name)
        except TypeError:
            # cause by bad constructor sig.
            print(self)
            raise
        return node


class AreaNodeHandlerHandler(TemplateNodeHandler):
    node = AreaNode

    def parse_init_args(self, node):
        data = node['data']
        rect = cast_list_float(data['rect'])
        units = data.get('units', None)
        try:
            dpi = float(data['dpi'])
        except KeyError:
            dpi = None
        return rect, units, dpi


class RootNodeHandler(TemplateNodeHandler):
    node = AreaNode

    def parse_init_args(self, node):
        try:
            if not node['name'] == 'root':
                raise JSONTemplateBuilder.SyntaxError
        except KeyError:
            # missing name
            raise JSONTemplateBuilder.SyntaxError

        data = node['data']
        rect = cast_list_float(data['rect'])

        try:
            units = data['units']
        except KeyError:
            raise JSONTemplateBuilder.SyntaxError

        try:
            dpi = float(data['dpi'])
        except KeyError:
            raise JSONTemplateBuilder.SyntaxError

        return rect, units, dpi


class ImageNodeHandlerHandler(TemplateNodeHandler):
    node = ImageNode

    def parse_init_args(self, node):
        filename = node.get('filename', None)
        return filename,  # the comma is not a mistake...leave it


class ImagePlaceholderNodeHandlerHandler(TemplateNodeHandler):
    node = ImagePlaceholderNode

    def parse_init_args(self, node):
        return None,


class TemplateBuilder:
    """Read a dict-based structure and create graph of TemplateNodes"""

    class SyntaxError(Exception):
        pass

    class UnrecognizedNodeTypeError(Exception):
        pass

    def __init__(self):
        self.handlers = {
            'root': RootNodeHandler(),
            'area': AreaNodeHandlerHandler(),
            'image': ImageNodeHandlerHandler(),
            'placeholder': ImagePlaceholderNodeHandlerHandler()
        }

    def build_graph(self, dict_graph):
        root = self.build_node(dict_graph)

        try:
            children = dict_graph['children']
        except KeyError:
            # no children, so just return the root node
            return root

        for child_graph in children:
            child = self.build_graph(child_graph)
            if child:
                root.add_child(child)

        return root

    def build_node(self, dict_graph):
        try:
            node_type = dict_graph['type']
        except KeyError:
            # missing the type name
            raise TemplateBuilder.SyntaxError

        try:
            handler = self.handlers[node_type]
        except KeyError:
            # this type is not handled
            raise TemplateBuilder.UnrecognizedNodeTypeError

        return handler.create_node(dict_graph)


class JSONTemplateBuilder(TemplateBuilder):
    def read(self, filename):
        with open(filename) as fp:
            json_graph = json.load(fp)

        return self.build_graph(json_graph)
