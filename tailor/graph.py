__all__ = ('Node',)


class Node:
    accepts = set()

    def __init__(self):
        self.parent = None
        self._children = list()

    @property
    def children(self):
        return list(self._children)

    def bfs_children(self):
        visited, stack = list(), [self]
        while stack:
            node = stack.pop()
            if node not in visited:
                visited.append(node)
                stack.extend(node.children)
        return reversed(visited[1:])

    def dfs_children(self):
        visited, stack = list(), [self]
        while stack:
            node = stack.pop(0)
            if node not in visited:
                visited.insert(0, node)
                stack.extend(node.children)
        return reversed(visited[:-1])

    def add_child(self, node):
        node.parent = self
        self._children.append(node)

    def push(self, node):
        """

        :param node:
        :type node:
        :return: True if accepted, otherwise False
        :rtype: bool
        """
        kind = type(node).__name__
        if kind in self.accepts:
            self.add_child(node)
            return True
        else:
            for child in self.children:
                if child.push(node):
                    return True
        return False

    def placeholders_needing_image(self):
        """ Generator that yields nodes that require an image
        """
        for child in self.dfs_children():
            if isinstance(child, ImagePlaceholderNode):
                if child.data is None:
                    yield child

    def parents(self):
        """not really fast since we don't have a ref to parents"""
        parent = self.parent
        while parent is not None:
            yield parent
            parent = parent.parent

    def determine_rect(self):
        """search through parents until a rect is found and return it
           if this node contains a rect, then return that
        """
        if hasattr(self, 'rect'):
            return self.rect
        else:
            return self.parent.determine_rect()

    def get_root(self):
        parent = self
        while parent.parent is not None:
            parent = parent.parent
        return parent


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
        for child in self.dfs_children():
            if isinstance(child, ImagePlaceholderNode):
                if child.data is None:
                    child.data = data
                    return


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
    accepts = (ImageNode,)

    def __init__(self, data, name=None):
        super().__init__()
        self.data = data
        self.name = name
