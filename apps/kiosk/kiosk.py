# -*- coding: utf-8 -*-
"""
Operator's kiosk for managing the photobooth
"""
import logging
import os
from functools import partial

from kivy.app import App
from kivy.config import Config
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager

from tailor.uix.picker import PickerScreen

logger = logging.getLogger("tailor.kiosk-loader")

DEFAULT_VKEYBOARD_LAYOUT = 'email'


class Manager(ScreenManager):
    pass


class KioskApp(App):
    manager = Manager()

    def build(self):
        return self.manager


def load_custom_kv_styles():
    jpath = os.path.join

    # make kiosk work without installing tailor into python
    app_root_path = os.path.realpath(os.path.join(__file__, '..', '..', '..'))

    styles_path = jpath(app_root_path, 'tailor', 'resources', 'styles')

    kv_files = (
        ('default', ('kiosk.kv',),),
    )

    for module, filenames in kv_files:
        func = partial(jpath, styles_path, module)
        for filename in filenames:
            Builder.load_file(func(filename))


def new():
    # set keyboard behaviour to be a little like IOS
    Config.set('kivy', 'keyboard_mode', 'dock')
    Config.set('kivy', 'keyboard_layout', DEFAULT_VKEYBOARD_LAYOUT)

    # set the display and touch screen up
    # TODO: load from cfg for customization
    Config.set('graphics', 'width', 1280)
    Config.set('graphics', 'height', 1024)
    Config.set('postproc', 'retain_time', 150)
    Config.set('postproc', 'retain_distance', 30)

    load_custom_kv_styles()

    app = KioskApp()
    app.manager.add_widget(PickerScreen(name='compositepicker'))

    return app
