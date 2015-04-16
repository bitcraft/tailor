import os
import shutil

from twisted.plugin import IPlugin
from twisted.internet import threads
from zope.interface import implements
from tailor import itailor


class FileCopy(object):
    implements(itailor.IFileOp)

    def __init__(self, dest, **kwargs):
        self.dest = dest
        self.overwrite = kwargs.get('overwrite', False)

    def process(self, filename):
        def func():
            path = os.path.join(self.dest, os.path.basename(filename))
            if not self.overwrite and os.path.exists(path):
                i = 1
                root, ext = os.path.splitext(path)
                path = "{0}-{1:04d}{2}".format(root, i, ext)
                while os.path.exists(path):
                    i += 1
                    path = "{0}-{1:04d}{2}".format(root, i, ext)

            shutil.copyfile(filename, path)
            return path

        if filename is None:
            raise ValueError

        return threads.deferToThread(func)


class FileCopyFactory(object):
    implements(IPlugin, itailor.iTailorPlugin)
    __plugin__ = FileCopy

    @classmethod
    def new(cls, *args, **kwargs):
        return cls.__plugin__(*args, **kwargs)


factory = FileCopyFactory()


