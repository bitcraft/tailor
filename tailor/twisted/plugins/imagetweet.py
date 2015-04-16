import pickle

from twisted.plugin import IPlugin
from twisted.internet import threads
import twython
from zope.interface import implements
from tailor import itailor


class ImageTweetFactory:
    implements(IPlugin)

    def new(self, *args, **kwargs):
        return ImageTweet(*args, **kwargs)


class ImageTweet:
    implements(itailor.IFileOp)

    def __init__(self):
        self._auth = None
        self._conn = None

    def auth(self, auth_file, *arg, **kwarg):
        with open(auth_file) as fh:
            self._auth = pickle.load(fh)['twitter']
        return self.connect()

    def process(self, msg, sender=None):
        def send(result):
            self._conn.update_status_with_media(msg, status='Test!')

        return threads.deferToThread(send)

    def connect(self):
        def conn(result):
            self._conn = result

        d = threads.deferToThread(twython.Twython, **self._auth)
        d.addCallback(conn)
        return d


factory = ImageTweetFactory
