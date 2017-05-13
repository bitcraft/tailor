"""

CAMERA PLUGINS

camera only operate with JPG images for now!

This requirement will change eventually.

"""
import logging

from . import composer, dummy_camera, filesystem

logger = logging.getLogger('tailor.plugins')


def get_camera():
    from tailor.config import pkConfig

    camera = None
    camera_cfg = pkConfig['camera']
    camera_plugin = camera_cfg['plugin']
    camera_name = camera_cfg['name']

    # TODO: Better error handling
    if camera_plugin == "dummy":
        camera = dummy_camera.DummyCamera()

    elif camera_plugin == "shutter":
        try:
            from . import shutter_camera
        except:
            pass

        else:
            if camera_name:
                import re
                regex = re.compile(camera_name)
            else:
                regex = None
            camera = shutter_camera.ShutterCamera(regex)

    elif camera_plugin == "opencv":
        try:
            from . import opencv_camera
        except ImportError:
            pass

        else:
            camera = opencv_camera.OpenCVCamera()

    elif camera_plugin == "pygame":
        try:
            from . import pygame_camera
        except:
            pass

        else:
            camera = pygame_camera.PygameCamera()

    if camera is None:
        logger.critical("cannot find camera plugin, using dummy")
        camera = dummy_camera.DummyCamera()

    return camera
