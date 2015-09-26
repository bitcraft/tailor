# -*- coding: utf-8 -*-
from glob import glob
from os.path import join
import os
import shutil
import re

from flask import Flask, request, jsonify, send_from_directory

from tailor.config import pkConfig

app = Flask(__name__)

monitor_folder = pkConfig['paths']['event_composites']
prints_folder = pkConfig['paths']['event_prints']
glob_string = '*png'
regex = re.compile('^(.*?)-(\d+)$')

config = dict()


def get_filenames_to_serve():
    folder = join(monitor_folder, 'original')
    return [build_url(os.path.basename(i))
            for i in glob(get_glob_string(folder))]


def get_glob_string(path):
    return join(path, glob_string)


def build_url(filename):
    url = '{protocol}://{host}:{port}'.format(**config)
    return '{}/files/{}'.format(url, filename)


@app.route('/files')
def get_files():
    files = {'files': get_filenames_to_serve()}
    return jsonify(files)


# TODO: move to real server (lighthttpd?)
@app.route('/files/<filename>')
def retrieve_file(filename):
    # TODO: accept arbitrary sizes and cache
    size = request.args.get('size', 'original')

    try:
        path = join(monitor_folder, size)
        return send_from_directory(path, filename)
    except:
        pass


def smart_copy(src, dest):
    path = os.path.join(dest, os.path.basename(src))

    root, ext = os.path.splitext(path)
    match = regex.match(root)
    if match:
        root, i = match.groups()
        i = int(i)
    else:
        i = 0

    if os.path.exists(path):
        i += 1
        path = "{0}-{1:04d}{2}".format(root, i, ext)
        while os.path.exists(path):
            i += 1
            path = "{0}-{1:04d}{2}".format(root, i, ext)

    shutil.copyfile(src, path)


@app.route('/print/<filename>')
def print_file(filename):
    src = os.path.join(prints_folder, filename)
    smart_copy(src, pkConfig['paths']['print_hot_folder'])
    return "ok"


def ServerApp():
    from tailor.net import guess_local_ip_addresses
    config.update(pkConfig['remote_server'])
    config['host'] = guess_local_ip_addresses()
    config['host'] = '127.0.0.1'
    return app
