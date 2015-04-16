from collections import defaultdict

"""
graph and nodes for plugin/workflow system
"""


class Graph:
    def __init__(self):
        self._graph = defaultdict(list)

    def update(self, node, children):
        self._graph[node] = children

    def children(self, node):
        return self._graph[node]

    def search(self, start):
        p = dict()
        q = list()
        q.append(start)
        p[start] = None
        while q:
            n = q.pop(0)
            yield p[n], n
            for c in self.children(n):
                p[c] = n
                q.append(c)
