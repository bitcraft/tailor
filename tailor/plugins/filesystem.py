# -*- coding: utf-8 -*-
import logging
import os
import re

from apps.service.session import regex

logger = logging.getLogger('tailor.filesystem')

regex = re.compile('^(.*?)-(\d+)$')


def incremental_naming(path):
    """ Utility method to find non-conflicting filenames

    Given a 'path' (ie: /user/boo/bar.baz) add numbers to the end
    of the file name, but before the extension, so that file names
    are unique.

    The containing folder, as determined by basename() will be
    searched for existing files that conflict with the name,
    and starting from 0, new numbers will be checked until
    the name is unique.

    Probably subject to race conditions, this needs review and locks.

    Do not use in situations where speed is needed!

    :param path: folder path + filename
    :return:
    """
    basename = os.path.basename(path)
    root, ext = os.path.splitext(path)

    match = regex.match(root)
    if match:
        root, i = match.groups()
        i = int(i)
    else:
        i = 0

    while os.path.exists(path):
        i += 1
        filename = "{0}-{1:04d}{2}".format(root, i, ext)
        path = os.path.join(basename, filename)
        if i > 9999:
            raise RuntimeError

    return path
