# -*- coding: utf-8 -*-
"""
script to run a local, self contained server

python 3.6 or higher required

currently is a candidate to use asyncio
"""
import logging
import time
import platform
import os
from os.path import split
from subprocess import Popen, call

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('tailor.launcher')

processes = (
    ('service_cmd', 'apps/service/__main__.py'),
    ('kiosk_server_cmd', 'apps/server/__main__.py'),
    ('kiosk_cmd', 'apps/kiosk/__main__.py'))

# TODO: find python cmd name on whatever platform
system = platform.system()

if system == 'Linux':
    python_cmd = '/usr/bin/python3'

elif system == 'Windows':
    python_cmd = "C:\\Users\\Leif\\AppData\\Local\\Programs\\Python\\Python36\\python.exe"


# TODO: use subprocess.run


def run_processes():
    for name, cmd in processes:
        logger.debug('starting process %s', name)
        args = [python_cmd, cmd]
        proc = Popen(args)
        time.sleep(2)
        yield proc


if __name__ == '__main__':
    # TODO: check for running in gnome environment
    # TODO: release_gvfs_from_camera fails in windows.  provide better check in future

    if system == 'Linux':
        from tailor.core.unix import release_gvfs_from_camera

        try:
            release_gvfs_from_camera()
        except FileNotFoundError:
            pass

    running_processes = list()

    try:
        for proc in run_processes():
            running_processes.append(proc)

        running = True
        while running:
            for proc in running_processes:
                value = proc.poll()
                if value is not None:
                    logger.debug('one process has quit')
                    running = False
                    break
                time.sleep(.1)

    except:
        import traceback

        traceback.print_last()
        logger.debug('an exception was raised and program will now terminate')

    finally:
        logger.debug('cleaning up...')
        for proc in running_processes:
            try:
                start = time.time()
                while proc.poll() is None:
                    if time.time() - start > 10:
                        break
                    try:
                        proc.terminate()
                        proc.kill()
                    except EnvironmentError:
                        pass

            # TODO: find the correct exception to catch
            except:
                pass

    # werkzerg/flask refuses to close using subprocess
    # so here is my heavy handed hack until i get it
    # figured out
    # TODO: better process cleanup
    if system == 'Linux':
        try:
            call(['killall', '-KILL', 'python3'], timeout=10)
        except FileNotFoundError:
            pass
