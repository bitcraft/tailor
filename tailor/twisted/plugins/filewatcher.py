from twisted.plugin import IPlugin
from twisted.internet import defer

from zope.interface import implements
from tailor import itailor
import watchdog


class FileWatcherFactory(object):
    implements(IPlugin)

    def new(self, *args, **kwargs):
        return FileWatcher(*args, **kwargs)


class FileWatcher(object):
    """
    Simple watcher that uses a glob to track new files
    This class will publish paths to new images
    """
    implements(itailor.IFileOp)

    def __init__(self, path, regex=None, recursive=False):
        self._path = path
        self._regex = regex
        self._recursive = recursive
        self._queue = defer.DeferredQueue()
        self.observer = None
        self.handler = None
        return self.reset()

    def reset(self):
        if self.observer is not None:
            self.observer.stop()

        if self.regex is None:
            self.handler = watchdog.FileSystemEventHandler()
        else:
            self.handler = watchdog.PatternMatchingEventHandler(self.regex)
        self.observer = watchdog.Observer()
        self.observer.schedule(self.handler, self._path, self._recursive)
        self.observer.start()
        return self.handler


factory = FileWatcherFactory()
