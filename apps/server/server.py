from glob import glob
from os.path import join
import os

from flask import Flask, request, jsonify, send_from_directory

from tailor.config import pkConfig

app = Flask(__name__)

monitor_folder = 'C:\\Users\\Leif\\events\\carrie-jon\\composites\\'
#  monitor_folder = '/Users/leif/events/heather-matt/composites/'
glob_string = '*png'

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


@app.route('/print/<filename>')
def print_file(filename):
    print(filename)
    return 'ok'


def ServerApp():
    from tailor.net import guess_local_ip_addresses
    config.update(pkConfig['remote_server'])
    config['host'] = guess_local_ip_addresses()
    return app
