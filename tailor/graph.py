__all__ = ('Node',)


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
            return True
        else:
            for child in self.children:
                if child.push(node):
                    return True
        return False
