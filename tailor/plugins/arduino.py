from zope.interface import implements

from tailor import itailor


class Arduino:
    implements(itailor.IFileOp)
