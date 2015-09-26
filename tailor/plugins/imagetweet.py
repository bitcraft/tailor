# -*- coding: utf-8 -*-
import pickle

import twython


class ImageTweet:
    def __init__(self):
        self._auth = dict()
        self._conn = None

    def auth(self, auth_file, *arg, **kwarg):
        with open(auth_file) as fh:
            self._auth = pickle.load(fh)['twitter']
        return self.connect()

    def process(self, msg, sender=None):
        self._conn.update_status_with_media(msg, status='Test!')

    def connect(self):
        twython.Twython(**self._auth)
