from twisted.plugin import IPlugin

from zope.interface import implements
from tailor import itailor


class Arduino:
    implements(IPlugin, itailor.IFileOp)
