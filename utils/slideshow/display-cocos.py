from multiprocessing import Process, Queue
import os
import subprocess
import random

import pyglet

import cocos
from cocos.actions import *
from cocos.scenes import *
from cocos.sprite import Sprite

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from utils.slideshow.worker import *

os.chdir('/home/mjolnir/git/tailor/slideshow')

pyglet.resource.reindex()

window = None

event = 'test'
# event_name = 'kali-joshua'


settings = {}
settings['shutter_sound'] = os.path.join('sounds', 'bell.wav')
settings['printsrv'] = '/home/mjolnir/smb-printsrv'
settings['template'] = 'templates/2x6vintage.template'
settings['thumbnails'] = '/home/mjolnir/events/{}/small'.format(event)
settings['detail'] = '/home/mjolnir/events/{}/medium'.format(event)
settings['originals'] = '/home/mjolnir/events/{}/originals'.format(event)
settings['composites'] = '/home/mjolnir/events/{}/composites/'.format(event)
settings['thumbnail_size'] = 768, 768
settings['large_size'] = 1024, 1024
settings['s_queue_size'] = 6
settings['l_queue_size'] = 3

workers = []
thumbnail_queue = Queue(settings['s_queue_size'])
image_queue = Queue(settings['l_queue_size'])


# worker just serves up images to use
def start_workers():
    global workers

    thumbnailer_p = Process(
        target=thumbnailer,
        args=(thumbnail_queue, settings))
    thumbnailer_p.start()

    loader_p = Process(
        target=loader,
        args=(image_queue, settings))
    loader_p.start()

    workers = [thumbnailer_p, loader_p]


def init():
    # disable screen blanking because it causes pyglet to lock
    subprocess.call(['xset', '-dpms'])
    subprocess.call(['xset', 's', 'off'])


def fetch_thumbnail():
    return thumbnail_queue.get()


def fetch_image():
    return image_queue.get()


class PanScanLayer(cocos.layer.Layer):
    def __init__(self):
        super(PanScanLayer, self).__init__()

        self._z = 0
        self.bkg = 0
        self.scale = 1.5
        self.interval = 5

        self.check_queue()

    def on_enter(self):
        cocos.layer.Layer.on_enter(self)
        self.unschedule(self.check_queue)
        self.schedule_interval(self.check_queue, self.interval)

    def on_exit(self):
        cocos.layer.Layer.on_exit(self)
        self.unschedule(self.check_queue)

    def check_queue(self, dt=0):
        width, height = cocos.director.director.get_window_size()

        if self.bkg:
            self.bkg.do(
                CallFunc(self.bkg.kill)
            )

        image = fetch_image()
        sprite = Sprite(image)

        end_scale = 1024.0 / image.width * self.scale

        sw = int((image.width * end_scale) / 2)
        sh = int((image.height * end_scale) / 2)

        if random.randint(0, 1):
            sprite.x = 0
        else:
            sprite.x = width

        sprite.y = random.randint(height * .25, height * .75)

        # dst = random.randint(width*.25, width*.75), height / 2
        dst = width / 2, height / 2

        sprite.scale = end_scale * 5
        sprite.opacity = 0
        sprite.do(
            spawn(
                FadeIn(1),
                AccelDeccel(
                    spawn(
                        ScaleTo(end_scale, duration=2),
                        MoveTo(dst, duration=2)))) +
            Delay(self.interval) +
            FadeOut(.5) +
            CallFunc(sprite.kill))

        self._z += 1
        self.add(sprite, z=self._z)


class ScrollingLayer(cocos.layer.Layer):
    def __init__(self):
        super(ScrollingLayer, self).__init__()

        self._side = random.randint(0, 1)
        self._last_sprite = None
        self._cached_size = None
        self.sprite_speed = 80.0

        self.batch = cocos.batch.BatchNode()
        self.add(self.batch)

    def on_enter(self):
        cocos.layer.Layer.on_enter(self)
        self.unschedule(self.check_sprites)
        self.schedule_interval(self.check_sprites, .25)

    def on_exit(self):
        cocos.layer.Layer.on_exit(self)
        self.unschedule(self.check_sprites)

    def check_sprites(self, dt=0):
        w_width, w_height = cocos.director.director.get_window_size()

        if self._last_sprite is None:
            y = w_height
        else:
            y = self._last_sprite.y

        if y > -w_height * .8:

            image = None
            if self._cached_size is None:
                image = fetch_thumbnail()
                self._cached_size = image.width, image.height

            image_height = self._cached_size[1]

            while y > -image_height:
                if image is None:
                    image = fetch_thumbnail()

                def check_position(dt, sprite, func):
                    if sprite.y - sprite.height / 2 > w_height:
                        sprite.unschedule(func)
                        sprite.kill()
                    else:
                        sprite.y += self.sprite_speed * dt

                if self._side:
                    self._side = 0
                    x = random.randint(image.width / 2,
                                       w_width / 2 - image.width / 2)
                else:
                    self._side = 1
                    x = random.randint(w_width / 2 + image.width / 2,
                                       w_width - image.width / 2)

                y -= image.height * .6

                sprite = Sprite(image, position=(x, y))
                sprite.schedule(check_position, sprite, check_position)

                self.batch.add(sprite)

                self._last_sprite = sprite

                if y > -image.height:
                    image = fetch_thumbnail()


class PhotoPileLayer(cocos.layer.Layer):
    def __init__(self):
        super(PhotoPileLayer, self).__init__()
        self.z = 0

        self.unschedule(self.check_queue)
        self.schedule_interval(self.check_queue, 1)

    def check_queue(self, dt=0):
        width, height = cocos.director.director.get_window_size()

        image = fetch_image()
        sprite = Sprite(image)

        sprite.rotation = random.randint(-25, 25)

        end_scale = 1024.0 / image.width

        sw = int((image.width * end_scale) / 2)
        sh = int((image.height * end_scale) / 2)

        sprite.x = random.randint(sw, width - sw)
        sprite.y = random.randint(sh, height - sh)

        sprite.opacity = 0
        sprite.scale = end_scale * 1.5

        sprite.do(
            spawn(
                FadeIn(.2),
                AccelDeccel(ScaleTo(end_scale, duration=.4))) +
            Delay(15) +
            FadeOut(.5) +
            CallFunc(sprite.kill))

        self.z += 1
        self.add(sprite, z=self.z)


class BackgroundLayer(cocos.layer.Layer):
    """
    class for showing images that fall onto a scrolling table cloth
    """

    def __init__(self, filename):
        super(BackgroundLayer, self).__init__()

        self.width, self.height = cocos.director.director.get_window_size()

        image = pyglet.image.load(filename)

        self.bkg0 = Sprite(image)
        self.bkg1 = Sprite(image)

        scale = float(self.width) / image.width
        self.bkg0.scale = scale
        self.bkg1.scale = scale

        self.bkg0.x = self.width / 2
        self.bkg1.x = self.width / 2
        self.bkg0.y = self.bkg0.height / 2

        self.add(self.bkg0)
        self.add(self.bkg1)

    def on_enter(self):
        cocos.layer.Layer.on_enter(self)
        self.unschedule(self.scroll)
        self.schedule(self.scroll)

    def on_exit(self):
        cocos.layer.Layer.on_exit(self)
        self.unschedule(self.scroll)

    def scroll(self, dt):
        # only tested for images scrolling up
        x = 0
        y = dt * 20.0

        self.bkg0.y += y
        self.bkg0.x += x

        self.bkg1.y = self.bkg0.y - self.bkg0.height

        if self.bkg1.y - self.bkg1.height / 2 > 0:
            self.bkg0.y -= self.bkg0.height
            self.bkg1.y = self.bkg0.y - self.bkg0.height


if __name__ == '__main__':
    import itertools
    import inspect

    import sys

    import cocos.scenes.transitions
    from cocos.layer.util_layers import ColorLayer


    # huge hack here
    all_transitions = []
    temp = dict(inspect.getmembers(cocos.scenes.transitions))

    transitions = [
        'FadeTransition',
        'ZoomTransition',
        'FlipX3DTransition',
    ]

    for name in transitions:
        all_transitions.append(temp[name])

    del temp, transitions

    def next_scene(dt=0):
        scene = next(all_scenes)()

        transition = random.choice(all_transitions)
        cocos.director.director.replace(transition(scene, duration=1))

    def panscan_scene(dt=0):
        pyglet.clock.schedule_once(next_scene, 15)
        scene = cocos.scene.Scene(
            PanScanLayer())
        return scene

    def pile_scene(dt=0):
        pyglet.clock.schedule_once(next_scene, 10)
        scene = cocos.scene.Scene(
            ColorLayer(255, 64, 64, 255),
            PhotoPileLayer())
        return scene

    def scroll_scene(dt=0):
        pyglet.clock.schedule_once(next_scene, 25)
        scene = cocos.scene.Scene(
            BackgroundLayer('../images/seamless-montage.png'),
            ScrollingLayer())
        return scene

    all_scenes = [panscan_scene, pile_scene, scroll_scene]
    all_scenes = itertools.cycle(all_scenes)

    start_workers()

    init()

    platform = pyglet.window.get_platform()
    display = platform.get_display("")
    screens = display.get_screens()

    pyglet.clock.set_fps_limit(60)

    cocos.director.director.init(fullscreen=True, screen=screens[-1])
    # cocos.director.director.init(fullscreen=True)

    try:
        cocos.director.director.run(next(all_scenes)())
    except KeyboardInterrupt:
        [p.terminate() for p in workers]
        cocos.director.director.terminate_app = True
    except:
        [p.terminate() for p in workers]
        raise
    finally:
        [p.terminate() for p in workers]
