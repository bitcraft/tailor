# -*- coding: utf-8 -*-
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

logger = logging.getLogger("tailor.kiosk-loader")

# make kiosk work without installing tailor into python
app_root_path = os.path.realpath(os.path.join(__file__, '..', '..', '..'))

DEFAULT_VKEYBOARD_LAYOUT = 'email'

# set keyboard behaviour to be a little like ios
Config.set('kivy', 'keyboard_mode', 'dock')
Config.set('kivy', 'keyboard_layout', DEFAULT_VKEYBOARD_LAYOUT)

# set the display up
Config.set('graphics', 'width', 1280)
Config.set('graphics', 'height', 1024)

# Config.set('graphics', 'fullscreen', 'auto')
# Config.set('graphics', 'fullscreen',
#            pkConfig.get('display', 'fullscreen'))
# Config.set('graphics', 'width',
#            pkConfig.getint('display', 'width'))
# Config.set('graphics', 'height',
#            pkConfig.getint('display', 'height'))

# the display/touch input i use needs some love
Config.set('postproc', 'retain_time',
           pkConfig.getint('kiosk', 'touch-retain-time'))
Config.set('postproc', 'retain_distance',
           pkConfig.getint('kiosk', 'touch-retain-distance'))

jpath = os.path.join
styles_path = jpath(app_root_path, 'tailor', 'resources', 'styles')
app_images_path = jpath(app_root_path, 'resources', 'images')

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
    # TODO: move to configuration (where it belongs!)
    # workaround to some defeciency in the sdl2 window backend
    # Window.fullscreen = 1
    # Window.fullscreen = 'fake'
    # Window.borderless = True

    app = KioskApp()
    app.manager.add_widget(PickerScreen(name='compositepicker'))

    return app
