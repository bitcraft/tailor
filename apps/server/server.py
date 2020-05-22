# -*- coding: utf-8 -*-
import atexit
import os
import re
import shutil
import threading
import time
from multiprocessing import Queue
from os.path import join

from flask import Flask, jsonify, request, send_from_directory

from tailor.config import pkConfig

app = Flask(__name__)

print_queue = Queue()
prints_folder = pkConfig["paths"]["event_prints"]
monitor_folder = pkConfig["paths"]["event_composites"]
glob_string = "*" + pkConfig["compositor"]["filetype"]
regex = re.compile("^(.*?)-(\d+)$")
config = dict()


class PrintQueueManager(threading.Thread):
    def run(self, *args, **kwargs):
        print_interval = pkConfig["server"]["print-queue"]["interval"]
        self.running = True
        while self.running:
            filename = print_queue.get()
            src = os.path.join(prints_folder, filename)
            smart_copy(src, "/home/retrobooth/smb-printsrv/")
            if print_interval:
                time.sleep(print_interval)

    def stop(self):
        self.running = False


def get_filenames_to_serve():
    try:
        with open(pkConfig["paths"]["event_log"]) as fp:
            return [build_url(i) for i in fp.read().strip().split("\n")]
    except IOError:
        return list()


def get_glob_string(path):
    return join(path, glob_string)


def build_url(filename):
    url = "{protocol}://{host}:{port}".format(**config)
    return "{}/files/{}".format(url, filename)


@app.route("/files")
def get_files():
    files = {"files": get_filenames_to_serve()}
    return jsonify(files)


@app.route("/files/<filename>")
def retrieve_file(filename):
    # TODO: accept arbitrary sizes and cache
    size = request.args.get("size", "original")

    try:
        path = join(monitor_folder, size)
        return send_from_directory(path, filename)
    except:
        pass


@app.route("/print/<filename>")
def enqueue_filename_for_print(filename):
    print_queue.put(filename)
    return "ok"


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


def ServerApp():
    config.update(pkConfig["remote_server"])
    # config['host'] = guess_local_ip_addresses()
    config["host"] = "127.0.0.1"
    config["SECRET_KEY"] = "secret!"

    print_queue_thread = PrintQueueManager()
    print_queue_thread.daemon = True
    print_queue_thread.start()

    # close thread when app exits.  i think.  probably just placebo, idk.
    atexit.register(print_queue_thread.stop)

    return app
