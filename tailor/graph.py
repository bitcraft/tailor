# -*- coding: utf-8 -*-
__all__ = ('Node',)


class Node:
    def __init__(self, kind, data):
        self.kind = kind
        self.name = None
        self.parent = None
        self.__dict__.update(data)
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

    def placeholders_needing_image(self):
        """ Generator that yields nodes that require an image
        """
        for child in self.dfs_children():
            if child.kind == 'placeholder':
                if not hasattr(child, 'data'):
                    yield child

    def needed_captures(self):
        """Search and return number of images needed
        """
        return len(list(self.placeholders_needing_image()))

    def push_image(self, data):
        for child in self.dfs_children():
            if child.kind == 'placeholder':
                if not hasattr(child, 'data'):
                    child.data = data
                    return

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
