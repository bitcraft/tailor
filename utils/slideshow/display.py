import pyglet


# some hacks for use on multihead setup
platform = pyglet.window.get_platform()
display = platform.get_display("")
screens = display.get_screens()
window = pyglet.window.Window(fullscreen=True, screen=screens[-1], vsync=0)

from pyglet.image import *
from pyglet.sprite import Sprite
from PIL import Image, ImageOps
import random, glob, os

from multiprocessing import Process, Queue
import subprocess

os.chdir('/home/mjolnir/git/tailor/slideshow/')

target_size = 800, 800
event_name = 'gunnar-dolly'

NEW_PHOTO_INTERVAL = 5

settings = {}
settings['originals'] = os.path.join('/', 'home', 'mjolnir', 'events', \
                                     event_name, 'originals')


def get_files():
    return glob.glob("{}/*jpg".format(settings['originals']))


def init():
    # disable screen blanking because it causes pyglet to lock
    subprocess.call(['xset', '-dpms'])
    subprocess.call(['xset', 's', 'off'])


def load_resize_and_convert(queue, filename):
    image = Image.open(filename)
    image = image.transpose(Image.FLIP_TOP_BOTTOM)
    image.thumbnail(target_size, Image.ANTIALIAS)
    image = ImageOps.expand(image, border=16, fill=(255, 255, 255))
    image = image.convert()
    w, h = image.size
    image = ImageData(w, h, image.mode, image.tostring())
    queue.put(image)


class TableclothDisplay:
    """
    class for showing images that fall onto a scrolling table cloth
    """

    def __init__(self, window, bkg_image, folder):
        self.background = pyglet.graphics.Batch()

        self.width, self.height = window.get_size()

        image = pyglet.image.load(bkg_image)

        self.bkg0 = Sprite(image, batch=self.background)
        self.bkg1 = Sprite(image, batch=self.background)

        self.bkg0.opacity = 128
        self.bkg1.opacity = 128

        scale = self.width / float(self.bkg0.width)
        self.bkg0.scale = scale
        self.bkg1.scale = scale

    def scroll(self, x, y):
        self.bkg0.y += y
        self.bkg0.x += x

        if self.bkg0.y >= self.bkg0.height:
            self.bkg0.y = 0

        if self.bkg0.y + self.bkg0.height <= self.height:
            self.bkg0.y = self.height

        self.bkg1.y = self.bkg0.y - self.bkg0.height - 1


load_queue = Queue()
images = []
image_batch = pyglet.graphics.Batch()
displayed = set()


def new_photo(dt=0):
    files = get_files()
    if not files: return
    new = set(files) - displayed
    if new:
        filename = random.choice(list(new))
        displayed.add(filename)
    else:
        filename = random.choice(files)
    p = Process(target=load_resize_and_convert, args=(load_queue, filename))
    p.start()


@window.event
def on_draw():
    display.background.draw()
    image_batch.draw()


def scroll(dt):
    display.scroll(0, dt * 20.0)

    to_remove = []
    for sprite in images:
        if sprite.y > window_size[1]:
            to_remove.append(sprite)

    for sprite in to_remove:
        images.remove(sprite)
        sprite.delete()

    dist = dt * 60.0
    for sprite in images:
        sprite.y += dist


side = 0


def check_queue(dt):
    global side

    try:
        image = load_queue.get(False)
    except:
        return

    else:
        if side:
            side = 0
            x = random.randint(0, window_size[0] / 2 - image.width)
        else:
            side = 1
            x = random.randint(window_size[0] / 2, window_size[0] - image.width)

        y = -image.height

        sprite = Sprite(image, x=x, y=y, batch=image_batch)
        images.append(sprite)


window_size = window.get_size()

if __name__ == '__main__':
    init()

    display = TableclothDisplay(window, '../images/seamless-montage.png', '.')

    pyglet.clock.set_fps_limit(120)
    pyglet.clock.schedule(scroll)
    pyglet.clock.schedule_interval(new_photo, NEW_PHOTO_INTERVAL)
    pyglet.clock.schedule_interval(check_queue, 1)

    new_photo()
    pyglet.app.run()
