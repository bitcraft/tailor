from unittest import TestCase
from tailor.template import *

class TestNode(TestCase):
    def test_node(self):
        self.assertFalse(Node().push(Node()))
        self.assertTrue(TemplateNode().push(ImageNode(None)))

        n0 = TemplateNode()
        n1 = TemplateNode()
        n2 = ImageNode(None)
        n0.push(n1)
        n1.push(n2)

        print('g', n0, n0.children)
        print('g', n1, n1.children)
        print('g', n2, n2.children)

        render_template_graph(n0)
        print(needed_captures(n0))

    def test_read_config(self):
        read_template_config('../resources/templates/2x6.template')
