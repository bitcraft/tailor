from functools import partial
import os
import logging
from urllib.parse import urlparse

from kivy.animation import Animation
from kivy.clock import Clock
from kivy.core.image import Image as CoreImage
from kivy.core.window import Window
from kivy.factory import Factory
from kivy.loader import Loader
from kivy.network.urlrequest import UrlRequest
from kivy.properties import *
from kivy.uix.screenmanager import Screen
from natsort import natsorted

from .effects import TailorScrollEffect
from .sharing import SharingControls
from .utils import search

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('tailor.picker')

OFFSET = 172
jpath = os.path.join
resource_path = os.path.realpath(jpath(__file__, '..', '..', 'resources'))
image_path = partial(jpath, resource_path, 'images')

polling_interval = 5


# TODO: move to more generic loader
def install_zc_listener(callback):
    from zeroconf import ServiceBrowser, Zeroconf
    import json

    filename = 'config/kiosk.json'
    with open(filename) as fp:
        json_data = json.load(fp)

    listeners = json_data['zeroconf-listeners']
    listener = listeners.pop()

    config = listener['config']
    service_type = config['type']

    zeroconf = Zeroconf()
    browser = ServiceBrowser(zeroconf, service_type, handlers=[callback])

    return zeroconf


class PickerScreen(Screen):
    """ A nice looking touch-enabled file browser
    """
    large_preview_size = ListProperty()
    small_preview_size = ListProperty()
    grid_rows = NumericProperty()
    images = ListProperty()

    def on_pre_enter(self):
        # set up the 'normal' state
        self.state = 'normal'

        # these are pulled from the .kv format file
        self.view = search(self, 'view')
        self.top_parent = search(self, 'top_parent')
        self.slider = search(self, 'slider')
        self.drawer = search(self, 'drawer')
        self.background = search(self, 'background')
        self.scrollview = search(self, 'scrollview')
        self.grid = search(self, 'grid')

        self.focus_widget = None

        # the grid will expand horizontally as items are added
        def f(widget, value):
            self.grid.width = value
            # self.slider.max = value

        self.grid.bind(minimum_width=f)

        # TODO: eventually make this related to the screen width, maybe
        self.grid.spacing = (64, 64)

        self.slider.max = 1

        # slider => scrollview binding
        def f(scrollview, widget, value):
            # not sure why value has to be negated here
            scrollview.effect_x.value = -value * self.grid.minimum_width

        self.slider.bind(value=partial(f, self.scrollview))

        # scrollview => slider binding
        def f(slider, widget, value):
            # avoid 'maximum recursion depth exceeded' error
            if value >= 0:
                slider.value = value

        self.scrollview.effect_x.bind(value=partial(f, self.slider))

        # background parallax effect
        def f(widget, value):
            if not self.locked:
                self.background.pos_hint = {'x': -value - .3, 'y': -.25}

        self.scrollview.bind(scroll_x=f)

        # kivy's scroll effect doesn't seem to work with a huge scrollview
        # so set the effect to my homebrew scrolling effect
        self.scrollview.effect_cls = TailorScrollEffect

        # tweak the loading so it is quick
        Loader.loading_image = CoreImage(image_path('loading.gif'))

        self.scrollview_hidden = False

        # P R E V I E W   L A B E L
        # the preview label is used with the focus widget is open
        self.preview_label = Factory.PreviewLabel(pos=(-1000, -1000))
        self.view.add_widget(self.preview_label)

        # the background has a parallax effect
        self.background.source = image_path('galaxy.jpg')
        self.background.pos_hint = {'x': 0}

        self.locked = False
        self.loaded = set()
        self.animated_widgets = list()
        self.remote_server = None

        install_zc_listener(self.on_new_zc_info)

        self.check_new_photos()
        Clock.schedule_interval(self.check_new_photos, polling_interval)

    def on_new_zc_info(self, zeroconf, service_type, name, state_change):
        from zeroconf import ServiceStateChange
        import socket

        if state_change is ServiceStateChange.Added:
            info = zeroconf.get_service_info(service_type, name)
            if info:
                self.remote_server = {'protocol': 'http',
                                      'host': socket.inet_ntoa(info.address),
                                      'port': info.port}

    def on_image_touch(self, widget, touch):
        """ called when any image is touched
        """
        if widget.collide_point(touch.x, touch.y):
            # hide the focus widget
            if self.scrollview_hidden:
                self.change_state('normal', widget=widget)

            # show the focus widget
            elif self.focus_widget is not widget:
                self.change_state('focus', widget=widget)

    def handle_new_images_response(self, req, results):
        images = set(results['files'])
        new = natsorted(images - self.loaded)

        if new:
            self.loaded.update(new)

            # retrieve small images, not large
            to_get = list()
            for url in new:
                new_url = url + '?size=small'
                to_get.append(new_url)

            self.fetch_images(to_get)

    def get_images(self):
        if self.remote_server is None:
            return

        url = '{protocol}://{host}:{port}/files'.format(**self.remote_server)
        on_success = self.handle_new_images_response
        req = UrlRequest(url, on_success)

    def fetch_images(self, new):
        for filename in new:
            widget = Factory.AsyncImage(
                source=filename,
                allow_stretch=True)
            widget.bind(on_touch_down=self.on_image_touch)
            self.grid.add_widget(widget)
        self.scroll_to_end()

    def check_new_photos(self, dt=None):
        """ Scan for new images and scroll to edge if found
        """
        self.get_images()

    def scroll_to_end(self):
        # scroll to edge
        if self.scrollview.effect_x is not None:
            Animation(
                value_normalized=1,
                t='in_out_quad',
                duration=1
            ).start(self.slider)

    def unlock(self, dt=None):
        self.locked = False

    def new_focus_widget(self, source):
        # the focus widget is the large preview image that is shown if the user
        # touches a small widget on the screen
        widget = Factory.AsyncImage(source=source)
        widget.allow_stretch = True
        widget.pos_hint = {'top': -1, 'center_x': .75}
        widget.height = self.height
        widget.bind(on_touch_down=self.on_image_touch)

        self.focus_widget = widget
        self.add_widget(widget)

    def stop_running_animations(self):
        for widget in self.animated_widgets:
            Animation.stop_all(widget)

        self.animated_widgets.clear()

    def change_state(self, state, **kwargs):
        if self.locked:
            return

        new_state = state
        old_state = self.state
        self.state = new_state
        transition = (old_state, self.state)

        logger.debug('transitioning state %s', transition)

        if transition == ('focus', 'normal'):
            self.stop_running_animations()
            self.transition_focus_normal(**kwargs)
        elif transition == ('normal', 'focus'):
            self.stop_running_animations()
            self.transition_normal_focus(**kwargs)
        else:
            print('invalid state:', state)
            raise RuntimeError

    def start_and_log(self, ani, target):
        self.animated_widgets.append(target)
        ani.start(target)

    def transition_focus_normal(self, *args, **kwargs):
        # ====================================================================
        # F O C U S  =>  N O R M A L
        screen_width, screen_height = self.view.size

        self.scrollview_hidden = False

        # close the keyboard
        Window.release_all_keyboards()

        # disable the controls (workaround until 1.8.0)
        self.controls.disable()

        # hide the controls
        ani = Animation(
            opacity=0.0,
            duration=.3)
        # ani.bind(on_complete=self._remove_widget_after_ani)
        ani.start(self.preview_label)
        if self.controls:
            self.start_and_log(ani, self.controls)

        # set the background to normal
        ani = Animation(
            size_hint=(3, 1.5),
            t='in_out_quad',
            duration=.5)
        self.start_and_log(ani, self.background)

        # show the scrollview and drawer
        ani = Animation(
            y=0,
            t='in_out_quad',
            opacity=1.0,
            duration=.5)
        self.start_and_log(ani, search(self, 'scrollview_area'))
        self.start_and_log(ani, self.drawer)

        # hide the focus widget
        ani = Animation(
            pos_hint={'top': 0},
            height=screen_height * .25,
            t='in_out_quad',
            duration=.5)

        ani &= Animation(
            opacity=0.0,
            duration=.5)

        self.start_and_log(ani, self.focus_widget)

        # schedule a unlock
        self.locked = True
        Clock.schedule_once(self.unlock, .5)

    def transition_normal_focus(self, *args, **kwargs):
        # =====================================================================
        #  N O R M A L  =>  F O C U S
        widget = kwargs['widget']
        self.scrollview_hidden = True

        # set the focus widget to have the same image as the one picked
        # do a bit of mangling to get a more detailed image

        # get a high resolution (full image_size) for the preview
        o = urlparse(widget.source)
        source = o.scheme + "://" + o.netloc + o.path
        self.new_focus_widget(source)

        # show the controls
        self.controls = SharingControls()
        self.controls.filename = source
        self.controls.size_hint = .40, 1
        self.controls.opacity = 0

        # animate showing the controls
        ani = Animation(
            opacity=1.0,
            duration=.3)
        self.start_and_log(ani, self.preview_label)
        self.start_and_log(ani, self.controls)

        self.preview_label.pos_hint = {'x': .25, 'y': .47}
        self.add_widget(self.controls)

        # hide the scrollview and drawer
        ani = Animation(
            x=0,
            y=-1000,
            t='in_out_quad',
            opacity=0.0,
            duration=.7)
        self.start_and_log(ani, search(self, 'scrollview_area'))
        self.start_and_log(ani, self.drawer)

        # start a simple animation on the background
        x = self.background.pos_hint['x']
        ani = Animation(
            t='in_out_quad',
            size_hint=(4, 2),
            duration=.5)
        ani += Animation(
            pos_hint={'x': x + 1.5},
            duration=480)
        self.start_and_log(ani, self.background)

        # show the focus widget
        ani = Animation(
            opacity=1.0,
            pos_hint={'top': 1, 'center_x': .75},
            size_hint=(1, 1),
            t='in_out_quad',
            duration=.5)
        ani &= Animation(
            opacity=1.0,
            duration=.5)
        self.start_and_log(ani, self.focus_widget)

        # schedule a unlock
        self.locked = True
        Clock.schedule_once(self.unlock, .5)
