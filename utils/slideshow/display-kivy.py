import kivy

kivy.require('1.5.0')

from kivy.config import Config

Config.set('graphics', 'fullscreen', True)

Config.set('graphics', 'width', '1920')
Config.set('graphics', 'height', '1080')

Config.set('graphics', 'show_cursor', False)
Config.set('graphics', 'show_mousecursor', False)

# performance tweaks
Config.set('graphics', 'multisamples', 0)

from kivy.animation import Animation
from kivy.app import App
from kivy.clock import Clock
from kivy.uix.image import Image
from kivy.uix.floatlayout import FloatLayout
from kivy.loader import Loader
from kivy.factory import Factory
from kivy.properties import *

import random, glob, os


target_size = 768, 768
event_name = 'gunnar-dolly'

settings = {}
settings['originals'] = os.path.join('/', 'home', 'mjolnir', 'events', \
                                     event_name, 'originals')



# Builder.load_file('display-kivy.kv')

Loader.num_workers = 3
Loader.max_upload_per_frame = 2


class CustomImage(Image):
    pass


Factory.register('CustomImage', CustomImage)


def get_files():
    return glob.glob("{}/*jpg".format(settings['originals']))


class SlideshowWidget(FloatLayout):
    image_duration = NumericProperty(3)
    new_image_interval = NumericProperty(1)


    def __init__(self, *arg, **kwarg):
        super(SlideshowWidget, self).__init__(*arg, **kwarg)

        self.image_size_hint = .40, .40

        Clock.schedule_interval(self.scan, self.new_image_interval)
        self.displayed = set()
        self.side = 0

    def destroy_widget(self, widget, arg):
        self.remove_widget(arg)

    def scan(self, dt):
        files = get_files()
        if not files: raise ValueError
        new = set(files) - self.displayed
        if new:
            filename = random.choice(list(new))
            self.displayed.add(filename)
        else:
            filename = random.choice(files)

        if self.side:
            self.side = 0
            pos_hint = {'x': random.random() / 4, 'top': .5}
        else:
            self.side = 1
            pos_hint = {'x': random.random() / 4 + .5, 'top': .5}

        image = Factory.AsyncImage(
            source=filename,
            pos_hint=pos_hint,
            size_hint=self.image_size_hint,
            nocache=True)
        self.add_widget(image)

    def add_widget(self, widget, *arg, **kwarg):
        super(SlideshowWidget, self).add_widget(widget, *arg, **kwarg)

        ani = Animation(
            t='linear',
            y=self.height,
            duration=self.image_duration)

        del widget.pos_hint['top']
        ani.bind(on_complete=self.destroy_widget)
        ani.start(widget)


class SlideshowApp(App):
    def build(self):
        return SlideshowWidget()


if __name__ == '__main__':
    import pygame

    app = SlideshowApp()

    # disable the default mouse arrow cursor
    pygame.init()
    pygame.mouse.set_visible(False)

    app.run()
