from functools import partial
import glob
import os
import logging

from kivy.animation import Animation
from kivy.clock import Clock
from kivy.core.image import Image as CoreImage
from kivy.factory import Factory
from kivy.loader import Loader
from kivy.uix.screenmanager import Screen
from kivy.properties import *
from ..config import pkConfig as pkConfig
from .sharing import SharingControls
from .utils import search
from .effects import TailorScrollEffect
from .utils import ArduinoHandler

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('tailor.picker')

OFFSET = 172
jpath = os.path.join
resource_path = os.path.realpath(jpath(__file__, '..', '..', 'resources'))
image_path = partial(jpath, resource_path, 'images')


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
        Loader.num_workers = pkConfig.getint('kiosk', 'loaders')
        Loader.max_upload_per_frame = pkConfig.getint('kiosk',
                                                      'max-upload-per-frame')

        self.scrollview_hidden = False

        # stuff for the arduino/tilt
        self.arduino_handler = ArduinoHandler()

        # F O C U S   W I D G E T
        # the focus widget is the large preview image that is shown if the user
        # touches a small widget on the screen
        self.focus_widget = Factory.FocusWidget(
            source=image_path('loading.gif'))
        self.focus_widget.allow_stretch = True
        self.focus_widget.pos_hint = {'top': -1, 'center_x': .75}
        self.focus_widget.height = self.height
        self.focus_widget.bind(on_touch_down=self.on_image_touch)
        self.add_widget(self.focus_widget)

        # P R E V I E W   L A B E L
        # the preview label is used with the focus widget is open
        self.preview_label = Factory.PreviewLabel(pos=(-1000, -1000))
        self.view.add_widget(self.preview_label)

        # the background has a parallax effect
        self.background.source = image_path('galaxy.jpg')
        self.background.pos_hint = {'x': 0}

        self.locked = False
        self.loaded = set()

        Clock.schedule_interval(self.check_new_photos, 1)

    def on_image_touch(self, widget, touch):
        """ called when any image is touched
        """
        if widget.collide_point(touch.x, touch.y):
            # hide the focus widget
            if self.scrollview_hidden:
                self.change_state('normal', widget=widget)

            # show the focus widget
            elif self.focus_widget is not widget:
                return False

    def check_new_photos(self, dt):
        """ Scan for new images and scroll to edge if found
        """

        new = self.get_images() - self.loaded

        for filename in sorted(new):
            self.loaded.add(filename)
            widget = Factory.AsyncImage(
                source=filename,
                allow_stretch=True)
            widget.bind(on_touch_down=self.on_image_touch)
            self.grid.add_widget(widget)

        # scroll to edge
        if new and self.scrollview.effect_x is not None:
            self.loaded |= new
            Animation(
                value_normalized=1,
                t='in_out_quad',
                duration=1
            ).start(self.slider)

    def _remove_widget_after_ani(self, ani, widget):
        self.remove_widget(widget)

    def unlock(self, dt=None):
        self.locked = False

    def change_state(self, state, **kwargs):
        if self.locked:
            return

        new_state = state
        old_state = self.state
        self.state = new_state
        transition = (old_state, self.state)

        logger.debug('transitioning state %s', transition)

        if transition == ('focus', 'normal'):
            self.transition_focus_normal(**kwargs)
        elif transition == ('normal', 'focus'):
            self.transition_normal_focus(**kwargs)
        else:
            print('invalid state:', state)
            raise RuntimeError

    def transition_focus_normal(self, *args, **kwargs):
        # ====================================================================
        # F O C U S  =>  N O R M A L
        screen_width, screen_height = self.view.size

        self.scrollview_hidden = False

        # cancel all running animations
        Animation.cancel_all(self.controls)
        Animation.cancel_all(self.scrollview)
        Animation.cancel_all(self.background)
        Animation.cancel_all(self.focus_widget)

        # close the keyboard
        from kivy.core.window import Window

        Window.release_all_keyboards()

        # disable the controls (workaround until 1.8.0)
        self.controls.disable()

        # hide the controls
        ani = Animation(
            opacity=0.0,
            duration=.3)
        ani.bind(on_complete=self._remove_widget_after_ani)
        ani.start(self.preview_label)
        if self.controls:
            ani.start(self.controls)

        # set the background to normal
        ani = Animation(
            size_hint=(3, 1.5),
            t='in_out_quad',
            duration=.5)
        ani.start(self.background)

        # show the scrollview and drawer
        ani = Animation(
            y=0,
            t='in_out_quad',
            opacity=1.0,
            duration=.5)
        ani.start(search(self, 'scrollview_area'))
        ani.start(self.drawer)

        # hide the focus widget
        ani = Animation(
            pos_hint={'top': 0},
            height=screen_height * .25,
            t='in_out_quad',
            duration=.5)

        ani &= Animation(
            opacity=0.0,
            duration=.5)

        ani.start(self.focus_widget)

        # schedule a unlock
        self.locked = True
        Clock.schedule_once(self.unlock, .5)

    def transition_normal_focus(self, *args, **kwargs):
        # =====================================================================
        #  N O R M A L  =>  F O C U S

        widget = kwargs['widget']
        self.scrollview_hidden = True

        # cancel all running animations
        Animation.cancel_all(self.scrollview)
        Animation.cancel_all(self.background)
        Animation.cancel_all(self.focus_widget)
        Animation.cancel_all(self.drawer)

        # set the focus widget to have the same image as the one picked
        # do a bit of mangling to get a more detailed image
        thumb, detail, original, comp = self.get_paths()
        filename = jpath(detail, os.path.basename(widget.source))
        original = jpath(original, os.path.basename(widget.source))

        # get a medium resolution image for the preview
        self.focus_widget.source = filename

        # show the controls
        self.controls = SharingControls()
        self.controls.filename = original
        self.controls.size_hint = .40, 1
        self.controls.opacity = 0

        ani = Animation(
            opacity=1.0,
            duration=.3)
        ani.start(self.preview_label)
        ani.start(self.controls)

        self.preview_label.pos_hint = {'x': .25, 'y': .47}
        self.add_widget(self.controls)

        # hide the scrollview and drawer
        ani = Animation(
            x=0,
            y=-1000,
            t='in_out_quad',
            opacity=0.0,
            duration=.7)
        ani.start(search(self, 'scrollview_area'))
        ani.start(self.drawer)

        # start a simple animation on the background
        x = self.background.pos_hint['x']
        ani = Animation(
            t='in_out_quad',
            size_hint=(4, 2),
            duration=.5)
        ani += Animation(
            pos_hint={'x': x + 1.5},
            duration=480)
        ani.start(self.background)

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
        ani.start(self.focus_widget)

        # schedule a unlock
        self.locked = True
        Clock.schedule_once(self.unlock, .5)

    @staticmethod
    def get_images():
        path = '~/events/carrie-jon/originals/'
        path = os.path.expanduser(path)
        path = os.path.normpath(path)
        return set(glob.glob('{0}/*.png'.format(path)))
