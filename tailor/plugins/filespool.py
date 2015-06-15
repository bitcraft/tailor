from zope.interface import implementer

from tailor import itailor


@implementer(itailor.IFileOp)
class FileSpool:
    def __init__(self):
        self.print_command = 'lpr'

    def process(self, msg, sender=None):
        cmd = [self.print_command, msg]
        return threads.deferToThread(subprocess32.call, cmd)
