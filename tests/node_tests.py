from unittest import TestCase
import json

from tailor.template import *
from tailor.graph import Node


class TestNode(TestCase):
    def test_node(self):
        self.assertFalse(Node().push(Node()))

    def test_render(self):
        renderer = TemplateRenderer()
        loader = JSONTemplateBuilder()
        root = loader.read('../tailor/resources/templates/test_template.json')

        from PIL import Image

        im = Image.new('RGB', (1024, 1024), (128, 0, 0))
        root.push_image(im)

        im = Image.new('RGB', (1024, 1024), (0, 128, 0))
        root.push_image(im)

        im = Image.new('RGB', (1024, 1024), (0, 0, 128))
        root.push_image(im)

        im = Image.new('RGB', (1024, 1024), (255, 255, 0))
        root.push_image(im)

        renderer.render(root)


class BuilderTests(TestCase):
    def build_root_node(self):
        node = {
            'type': 'area',
            'name': 'root',
            'data': {
                'dpi': 72,
                'units': 'inches',
                'rect': [0, 0, 2, 6]
            },
            'children': []
        }
        return node

    def test_root_not_area_type_raises_syntaxerror(self):
        node = self.build_root_node()
        node['type'] = 'image'
        loader = JSONTemplateBuilder()
        with self.assertRaises(JSONTemplateBuilder.SyntaxError):
            loader.build_root_node(node)

    def test_root_not_named_root_raises_syntaxerror(self):
        node = self.build_root_node()
        node['name'] = 'not_root'
        loader = JSONTemplateBuilder()
        with self.assertRaises(JSONTemplateBuilder.SyntaxError):
            loader.build_root_node(node)

    def test_root_missing_name_raises_syntaxerror(self):
        node = self.build_root_node()
        del node['name']
        loader = JSONTemplateBuilder()
        with self.assertRaises(JSONTemplateBuilder.SyntaxError):
            loader.build_root_node(node)

    def test_root_missing_dpi_raises_syntaxerror(self):
        node = self.build_root_node()
        del node['data']['dpi']
        loader = JSONTemplateBuilder()
        with self.assertRaises(JSONTemplateBuilder.SyntaxError):
            loader.build_root_node(node)

    def test_root_missing_units_raises_syntaxerror(self):
        node = self.build_root_node()
        del node['data']['units']
        loader = JSONTemplateBuilder()
        with self.assertRaises(JSONTemplateBuilder.SyntaxError):
            loader.build_root_node(node)

    def test_read_list_convert_float_good_rect_int(self):
        test_string = """{"rect": [0, 0, 2, 4]}"""
        data = json.loads(test_string)
        loader = JSONTemplateBuilder()
        self.assertEqual(loader.cast_list_float(data['rect']),
                         [0, 0, 2, 4])

    def test_read_list_convert_float_good_rect_float(self):
        test_string = """{"rect": ["0.0", "0.1", "2.5", ".4"]}"""
        data = json.loads(test_string)
        loader = JSONTemplateBuilder()
        self.assertEqual(loader.cast_list_float(data['rect']),
                         [0.0, 0.1, 2.5, .4])

    def test_read_list_convert_float_rect_bad_raises_syntaxerror(self):
        test_string = """{"rect": ["0.0", "AAA", "2.5", ".4"]}"""
        data = json.loads(test_string)
        loader = JSONTemplateBuilder()
        with self.assertRaises(JSONTemplateBuilder.SyntaxError):
            loader.cast_list_float(data['rect'])

    def test_missing_type_raises_syntaxerror(self):
        test_string = """{"data": [1,2,3]}"""
        data = json.loads(test_string)
        loader = JSONTemplateBuilder()
        with self.assertRaises(JSONTemplateBuilder.SyntaxError):
            loader.build_node(data)

    def test_missing_data_raises_syntaxerror(self):
        test_string = """{"type": "area"}"""
        data = json.loads(test_string)
        loader = JSONTemplateBuilder()
        with self.assertRaises(JSONTemplateBuilder.SyntaxError):
            loader.build_node(data)

    def test_invalid_node_type_raises_valueerror(self):
        test_string = """{"type": "invalid_node_type", "data": "data"}"""
        data = json.loads(test_string)
        loader = JSONTemplateBuilder()
        with self.assertRaises(ValueError):
            loader.build_node(data)
