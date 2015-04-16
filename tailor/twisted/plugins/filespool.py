from twisted.plugin import IPlugin
from twisted.internet import threads

from zope.interface import implements
from tailor import itailor
import subprocess32


class FileSpool:
    implements(itailor.IFileOp)

    def __init__(self):
        self.print_command = 'lpr'

    def process(self, msg, sender=None):
        cmd = [self.print_command, msg]
        return threads.deferToThread(subprocess32.call, cmd)


class FileSpoolFactory:
    implements(IPlugin, itailor.iTailorPlugin)
    __plugin__ = FileSpool

    @classmethod
    def new(cls, *args, **kwargs):
        return cls.__plugin__(*args, **kwargs)


factory = FileSpoolFactory()
