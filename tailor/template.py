"""
utilities for templates
"""
import configparser


# def needed_captures(template):
#     captures = 0
#     for section in template.sections():
#         try:
#             if template.get(section, 'filename').lower() == 'auto':
#                 captures += 1
#         except:
#             pass
#     return captures

def build_image_node(kwargs):
    pass


def read_template_config(filename):
    config = configparser.ConfigParser()
    config.read(filename)
    # config.read(pkConfig['paths']['event_template'])

    head = TemplateNode()

    for section in sorted(config.sections()):
        if section == 'general':
            # node = TemplateNode()
            pass
        else:
            node = ImageNode(None)
            head.push(node)

    print(needed_captures(head))

    return head

def needed_captures(node):
    """Search and return number of images needed

    :param node:
    :type node:
    :return:
    :rtype:
    """
    needed = 0
    for child in node.dfs_children():
        if isinstance(child, ImageNode):
            if child.data is None:
                needed += 1
    return needed


def render_template_graph(node):
    for node in node.dfs_children():
        pass


class Node:
    accepts = set()

    def __init__(self):
        self.children = list()

    def bfs_children(self):
        visited, stack = list(), [self]
        while stack:
            node = stack.pop()
            if node not in visited:
                visited.append(node)
                stack.extend(node.children)
        return visited

    def dfs_children(self):
        visited, stack = list(), [self]
        while stack:
            node = stack.pop(0)
            if node not in visited:
                visited.insert(0, node)
                stack.extend(node.children)
        return visited

    def push(self, node):
        """

        :param kind:
        :type kind:
        :param node:
        :type node:
        :return: True if accepted, otherwise False
        :rtype: bool
        """
        kind = type(node).__name__
        if kind in self.accepts:
            self.children.append(node)
            return node
        else:
            for child in self.children:
                if child.push(node):
                    return node
            return None


class TemplateNode(Node):
    """
    node represents a template
    """
    accepts = {'TemplateNode', 'ImageNode'}

    def __init__(self):
        super().__init__()


class ImageNode(Node):
    """
    represents an image
    """

    def __init__(self, data):
        super().__init__()
        self.data = data
