import os
import shutil
import asyncio

from zope.interface import implementer
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler, FileSystemEventHandler

from tailor import itailor


@implementer(itailor.IFileOp)
class FileCopy:
    def __init__(self, dest, **kwargs):
        self.dest = dest
        self.overwrite = kwargs.get('overwrite', False)

    def process(self, filename):
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


@implementer(itailor.IFileOp)
class FileDelete:
    def process(self, msg):
        os.unlink(msg)


@implementer(itailor.IFileOp)
class FileWatcher:
    """
    Simple watcher that uses a glob to track new files
    This class will publish paths to new images
    """

    def __init__(self, path, regex=None, recursive=False):
        self._path = path
        self._regex = regex
        self._recursive = recursive
        self._queue = asyncio.Queue()
        self._observer = None
        self.handler = None

    def reset(self):
        if self._observer is not None:
            self._observer.stop()

        if self._regex is None:
            self.handler = FileSystemEventHandler()
        else:
            self.handler = PatternMatchingEventHandler(self._regex)
        self._observer = Observer()
        self._observer.schedule(self.handler, self._path, self._recursive)
        self._observer.start()
        return self.handler

