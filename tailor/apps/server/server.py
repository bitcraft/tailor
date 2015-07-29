from glob import glob
from flask import Flask, jsonify, send_from_directory
import os

app = Flask(__name__)


monitor_folder = 'C:\\Users\\Leif\\events\\carrie-jon\\composites\\'
glob_string = '*png'
local_addr = ('127.0.0.1', 5000)


def get_filenames_to_serve():
    return [build_url(os.path.basename(i)) for i in glob(get_glob_string(monitor_folder))]


def get_glob_string(path):
    return path + glob_string


def build_url(filename):
    addr, port = local_addr
    return 'http://{}:{}/files/{}'.format(addr, port, filename)


@app.route('/files')
def get_files():
    files = {'files': get_filenames_to_serve()}
    return jsonify(files)


# TODO: move to real server (lighthttpd?)
@app.route('/files/<filename>')
def retrieve_file(filename):
    return send_from_directory(monitor_folder, filename)


@app.route('/print/<filename>')
def print_file(filename):
    print(filename)
    return 'ok'


def ServerApp():
    return app
