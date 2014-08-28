from twisted.plugin import IPlugin

from zope.interface import implements
from tailor import itailor


class Arduino(object):
    implements(IPlugin, itailor.IFileOp)
