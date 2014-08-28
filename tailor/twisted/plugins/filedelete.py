import os

from twisted.plugin import IPlugin
from twisted.internet import threads

from zope.interface import implements
from tailor import itailor


class FileDelete(object):
    implements(itailor.IFileOp)

    def process(self, msg, sender=None):
        return threads.deferToThread(os.unlink, msg)


class FileDeleteFactory(object):
    implements(IPlugin, itailor.iTailorPlugin)
    __plugin__ = FileDelete

    @classmethod
    def new(cls, *args, **kwargs):
        return cls.__plugin__(*args, **kwargs)


factory = FileDeleteFactory()
