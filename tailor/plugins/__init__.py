import logging

from . import composer, dummy_camera, filesystem

logger = logging.getLogger('tailor.plugins')

try:
    from . import opencv_camera
except ImportError:
    pass

# TODO: fix in shutter!
# error is caused when libgphoto is not found
try:
    from . import shutter_camera
except:
    logger.debug('cannot load shutter plugin')
    pass

try:
    from . import pygame_camera
except:
    pass


def get_camera():
    from tailor.config import pkConfig

    camera_cfg = pkConfig['camera']
    camera_plugin = camera_cfg['plugin']
    camera_name = camera_cfg['name']

    # TODO: Error handling
    if camera_plugin == "dummy":
        camera = dummy_camera.DummyCamera()

    elif camera_plugin == "shutter":
        if camera_name:
            import re
            regex = re.compile(camera_name)
        else:
            regex = None
        camera = shutter_camera.ShutterCamera(regex)

    elif camera_plugin == "opencv":
        camera = opencv_camera.OpenCVCamera()

    elif camera_plugin == "pygame":
        camera = pygame_camera.PygameCamera()

    else:
        logger.critical("cannot find camera plugin")
        raise RuntimeError

    return camera
