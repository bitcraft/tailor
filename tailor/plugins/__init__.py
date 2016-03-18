from . import composer
from . import dummy_camera
from . import filesystem

try:
    from . import opencv_camera
except ImportError:
    pass

# TODO: fix in shutter!
# error is caused when libgphoto is not found
try:
    from . import shutter_camera
except:
    pass

try:
    from . import pygame_camera
except:
    pass
