import os

from zope.interface import implements

from tailor import itailor


class FileDelete:
    implements(itailor.IFileOp)

    def process(self, msg, sender=None):
        return threads.deferToThread(os.unlink, msg)


class FileDeleteFactory:
    implements(itailor.iTailorPlugin)
    __plugin__ = FileDelete

    @classmethod
    def new(cls, *args, **kwargs):
        return cls.__plugin__(*args, **kwargs)


factory = FileDeleteFactory()
