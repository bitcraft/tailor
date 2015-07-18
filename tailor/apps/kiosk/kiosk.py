#!/usr/bin/env python
"""
Operator's kiosk for managing the photobooth
"""
import os
from functools import partial
import logging

from kivy.config import Config
from kivy.app import App
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager
from tailor.config import pkConfig as pkConfig
from tailor.uix.picker import PickerScreen

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("tailor.kiosk-loader")

# make kiosk work without installing tailor into python
app_root_path = os.path.realpath(os.path.join(__file__, '..', '..', '..', '..'))
# sys.path.append(app_root_path)
# sys.path.append(os.path.join(app_root_path, 'tailor'))


DEFAULT_VKEYBOARD_LAYOUT = 'email'

# because i hate typing
jpath = os.path.join

# set keyboard behaviour to be a little like ios
Config.set('kivy', 'keyboard_mode', 'dock')
Config.set('kivy', 'keyboard_layout', DEFAULT_VKEYBOARD_LAYOUT)

# set the display up
Config.set('graphics', 'fullscreen',
           pkConfig.get('display', 'fullscreen'))
Config.set('graphics', 'width',
           pkConfig.getint('display', 'width'))
Config.set('graphics', 'height',
           pkConfig.getint('display', 'height'))

# the display/touch input i use needs some love
Config.set('postproc', 'retain_time',
           pkConfig.getint('kiosk', 'touch-retain-time'))
Config.set('postproc', 'retain_distance',
           pkConfig.getint('kiosk', 'touch-retain-distance'))

# paths
# all_images_path = os.path.abspath(pkConfig.get('paths', 'images'))
# event_name = pkConfig.get('event', 'name')
# event_images_path = jpath(all_images_path, event_name)
# composites_path = jpath(event_images_path, 'composites')
styles_path = jpath(app_root_path, 'tailor', 'resources', 'styles')
app_images_path = jpath(app_root_path, 'resources', 'images')
# paths = ('thumbnails', 'detail', 'originals', 'composites')

kv_files = (
    ('default', ('kiosk.kv',),),
)

for module, filenames in kv_files:
    func = partial(jpath, styles_path, module)
    for filename in filenames:
        Builder.load_file(func(filename))


class Manager(ScreenManager):
    pass


class KioskApp(App):
    manager = Manager()

    def build(self):
        return self.manager


def new():
    # pygame is not default installed on windows kivy portable pkg
    # import pygame
    #
    # if pkConfig.getboolean('display', 'hide-mouse'):
    #     cursor = pygame.cursors.load_xbm(
    #         os.path.join(app_images_path, 'blank-cursor.xbm'),
    #         os.path.join(app_images_path, 'blank-cursor-mask.xbm'))
    #     pygame.mouse.set_cursor(*cursor)

    app = KioskApp()
    app.manager.add_widget(PickerScreen(name='compositepicker'))
    return app
