""" Support loading template graphs from json formatted files
"""
import json

from tailor.graph import Node

__all__ = ['cast_list_float',
           'TemplateBuilder',
           'JSONTemplateBuilder',
           'create_root_node',
           'create_area_node',
           'create_image_node']


def cast_list_float(values):
    """

    :param values: list of stuff
    :return: list of stuff as floats
    :raises: ValueError TypeError
    """
    try:
        return [float(i) for i in values]
    except (ValueError, TypeError):
        raise TemplateBuilder.SyntaxError


def create_area_node(json_graph):
    data = json_graph['data']
    rect = cast_list_float(data['rect'])
    units = data.get('units', None)
    try:
        dpi = float(data['dpi'])
    except KeyError:
        dpi = None
    return Node('area', {'rect': rect, 'units': units, 'dpi': dpi})


def create_root_node(json_graph):
    if not json_graph['name'] == 'root':
        raise JSONTemplateBuilder.SyntaxError

    data = json_graph['data']
    rect = cast_list_float(data['rect'])
    units = data['units']
    dpi = float(data['dpi'])
    return Node('area', {'rect': rect, 'units': units, 'dpi': dpi})


def create_image_node(json_graph):
    return Node('image', {'filename': json_graph['data']['filename']})


def create_placeholder_node(json_graph):
    return Node('placeholder', json_graph['data'])


class TemplateBuilder:
    """Read a dict-based structure and create graph of TemplateNodes"""

    class SyntaxError(Exception):
        pass

    class UnrecognizedNodeTypeError(Exception):
        pass

    def __init__(self):
        self.handlers = {
            'root': create_root_node,
            'area': create_area_node,
            'image': create_image_node,
            'placeholder': create_placeholder_node
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

        try:
            node = handler(dict_graph)
        except KeyError:
            # all handlers get args from dict, so a KeyError
            # indicates the required info. is missing
            print(node_type, dict_graph)
            raise TemplateBuilder.SyntaxError

        return node

class JSONTemplateBuilder(TemplateBuilder):
    def read(self, filename):
        with open(filename) as fp:
            json_graph = json.load(fp)

        return self.build_graph(json_graph)
