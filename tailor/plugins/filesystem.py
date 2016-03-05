# -*- coding: utf-8 -*-
import logging
import os
import re

logger = logging.getLogger('tailor.filesystem')

regex = re.compile('^(.*?)-(\d+)$')


def _incremental_naming(path):
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

    return i, path


def highest_numbered_file_with_prefix(path):
    """ Utility method to find non-conflicting filenames

    Given a 'path' (ie: /user/boo/bar.baz) add numbers to the end
    of the file name, but before the extension, so that file names
    are unique.

    if the filename passed does not exist, then it will be returned,
    if the filename is found, then the next id will be checked

    This function returns the numeral of the highest filename + 1,
    so it is safe to assume that there are no conflicts.

    Probably subject to race conditions, this needs review and locks.
    Do not use in situations where speed is needed!

    :type path: basestring
    :rtype: int
    """
    return _incremental_naming(path)[0]


def incremental_naming(path):
    """ Utility method to find non-conflicting filenames

    Given a 'path' (ie: /user/boo/bar.baz) add numbers to the end
    of the file name, but before the extension, so that file names
    are unique.

    if the filename passed does not exist, then it will be returned,
    if the filename is found, then the next id will be checked

    This function returns the numeral of the highest filename + 1,
    so it is safe to assume that there are no conflicts.

    Probably subject to race conditions, this needs review and locks.
    Do not use in situations where speed is needed!

    :type path: basestring
    :rtype: basestring
    """
    return _incremental_naming(path)[1]
