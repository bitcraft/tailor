import logging
from subprocess import call

logger = logging.getLogger("tailor.platform.unix")


def release_gvfs_from_camera():
    """ Release the greedy fingers of gnome from the camera
    
    Gnome will capture a camera every time it is plugged in or power cycled.
    Thes function will force gnome to unmount the camera.
    
    :return: None 
    """
    logger.debug("releasing camera from gvfs...")
    call(["gvfs-mount", "-s", "gphoto2"], timeout=10)
