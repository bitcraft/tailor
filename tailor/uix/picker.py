# -*- coding: utf-8 -*-
import io
import logging
import os
import queue
from functools import partial
from urllib.parse import urlparse

from kivy.animation import Animation
from kivy.clock import Clock
from kivy.core.image import Image as CoreImage
from kivy.core.window import Window
from kivy.factory import Factory
from kivy.graphics.texture import TextureRegion
from kivy.loader import Loader
from kivy.network.urlrequest import UrlRequest
from kivy.properties import *
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen
from natsort import natsorted

from .camera import PreviewHandler
from .effects import TailorScrollEffect
from .sharing import SharingControls
from .utils import search, trigger_session_via_socket

logger = logging.getLogger("tailor.picker")

OFFSET = 172
jpath = os.path.join
resource_path = os.path.realpath(jpath(__file__, "..", "..", "resources"))
image_path = partial(jpath, resource_path, "images")

polling_interval = 5


class PickerScreen(Screen):
    """ A nice looking touch-enabled file browser
    """

    large_preview_size = ListProperty()
    small_preview_size = ListProperty()
    grid_rows = NumericProperty()
    images = ListProperty()

    def on_pre_enter(self):
        # set up the 'normal' state
        self.state = "normal"

        # these are pulled from the .kv format file
        self.view = search(self, "view")
        self.top_parent = search(self, "top_parent")
        self.drawer = search(self, "drawer")
        self.background = search(self, "background")
        self.scrollview = search(self, "scrollview")
        self.grid = search(self, "grid")

        # TODO: eventually make this related to the screen width, maybe
        self.grid.spacing = (64, 64)

        # the grid will expand horizontally as items are added
        def f(widget, value):
            self.grid.width = value

        self.grid.bind(minimum_width=f)

        # background parallax effect
        def f(widget, value):
            if not self.locked:
                self.background.pos_hint = {"x": -value - 0.3, "y": -0.25}

        self.scrollview.bind(scroll_x=f)

        # kivy's scroll effect doesn't seem to work with a huge scrollview
        # so set the effect to my homebrew scrolling effect
        self.scrollview.effect_cls = TailorScrollEffect
        self.scrollview_hidden = False

        # set loading image to an ugly spinning gif
        Loader.loading_image = CoreImage(image_path("loading.gif"))

        # the preview label is used with the focus widget is open
        self.preview_texture = None
        self.preview_label = Factory.PreviewLabel(pos=(-1000, -1000))
        self.view.add_widget(self.preview_label)

        #   E X I T   B U T T O N
        # this button is used to exit the large camera preview window
        def exit_preview(widget, touch):
            if widget.collide_point(touch.x, touch.y):
                self.change_state("normal")

        self.preview_exit = Factory.ExitButton(source=image_path("chevron-right.gif"))
        self.preview_exit.bind(on_touch_down=exit_preview)
        self.preview_exit.size_hint = None, None
        self.preview_exit.width = 64
        self.preview_exit.height = 175
        # self.preview_exit.x = 1280
        # self.preview_exit.y = (1024 / 2) - (self.preview_exit.height / 2)
        self.preview_exit.pos_hint = {"x": 1, "center_y": 0.5}
        self.view.add_widget(self.preview_exit)

        #  P R E V I E W   B U T T O N
        button = search(self, "previewbutton")
        button.bind(on_press=self.toggle_preview)
        self.preview_button = button

        #  P R E V I E W   B U T T O N
        button = search(self, "adjustmentbutton")
        button.bind(on_press=self.toggle_adjustment)
        self.adjustment_button = button

        # the background has a parallax effect
        self.background.source = image_path("galaxy.jpg")
        self.background.pos_hint = {"x": 0}

        self.locked = False
        self.loaded = set()
        self.animated_widgets = list()

        # TODO: do not hardcode
        self.remote_server = {"protocol": "http", "host": "127.0.0.1", "port": 5000}

        self.focus_widget = None

        self.check_new_photos()
        Clock.schedule_interval(self.check_new_photos, polling_interval)

        #  C O U N T D O W N   L A B E L
        font_name = "tailor/resources/fonts/Market_Deco.ttf"
        self.countdown_label = Label(font_size=400, font_name=font_name)
        self.countdown_label.text_size = None, None
        self.countdown_label.size_hint = (1, 1)
        self.countdown_label.pos_hint = {"x": 0, "y": 0}
        self.countdown_label.opacity = 0.85
        self.overlay_text = None

        # TODO: fix this
        self.overlay_text = None
        self.scheduled_return_to_normal = False

        # TODO: needs to be phased out
        # queueing them and updating the widget's texture
        self.preview_widget = None

    def toggle_preview(self, *args, **kwargs):
        if self.state == "normal":
            trigger_session_via_socket()
            self.change_state("preview")
        elif self.state == "preview":
            self.change_state("normal")

    def toggle_adjustment(self, *args, **kwargs):
        if self.state == "normal":
            self.change_state("adjustment")
        elif self.state == "adjustment":
            self.change_state("normal")

    @staticmethod
    def update_texture(texture, image_data):
        # needed when opengl context is lost...not worried about that now

        # TODO: file extension testing
        # load a image from bytes,
        # but also keep the data, so the texture can be reused
        data = io.BytesIO(image_data)
        data = (
            CoreImage(data, ext="jpg", nocache=True, keep_data=True).image._data[0].data
        )

        texture.blit_buffer(data)
        texture.flip_vertical()
        texture.flip_horizontal()

    def create_preview_texture(self, initial_data, aspect):
        # TODO: file extension testing
        data = io.BytesIO(initial_data)
        image = CoreImage(data, ext="jpg", nocache=True)
        texture = image.texture

        # add_reload_observer is required for loading texture info
        # after the openGL context is lost and images need to be reloaded
        # currently, losing opengl context is not tested
        texture.add_reload_observer(self.update_texture)
        texture.flip_horizontal()

        # TODO: only works for wide images!
        h = image.height
        w = image.height * aspect
        x = (image.width - w) / 2
        y = 0
        region = TextureRegion(x, y, w, h, texture)

        self.preview_data = texture
        self.preview_texture = region

    def set_preview_texture(self, imdata, aspect):
        # textures must be created in the main thread;
        # this is a limitation in pygame
        if self.preview_texture is None:
            self.create_preview_texture(imdata, aspect)
        else:
            self.update_texture(self.preview_data, imdata)

        return self.preview_texture

    def set_preview_widget(self):
        self.preview_widget = Image(texture=self.preview_texture, nocache=True)
        self.preview_widget.allow_stretch = True
        self.preview_widget.size_hint = 0.95, 1
        self.preview_widget.pos_hint = {"center_x": 0.5, "y": 1}
        # self.preview_widget.bind(on_touch_down=self.on_touch_down)
        self.add_widget(self.preview_widget)

    def get_packet_from_queue(self):
        """ Eventually move to a generic camera widget

        :return:
        """
        # want to block on the first frame
        block = self.preview_widget is None
        try:
            return self.preview_handler.queue.get(block)
        except queue.Empty:
            return None

    # P R E V I E W   W I D G E T
    def update_preview(self, *args, **kwargs):
        packet = self.get_packet_from_queue()

        if packet:
            session = packet["session"]
            imdata = packet["image_data"]
            aspect = packet["aspect_ratio"]

            self.set_preview_texture(imdata, aspect)
            if self.preview_widget is None:
                self.set_preview_widget()

            if self.state == "preview":
                self.set_preview_overlay_text(session)

    def set_preview_overlay_text(self, session):
        # TODO: 'session', needs some documentation
        def end_state(dt):
            self.countdown_label.text = ""
            self.change_state("normal")
            self.scheduled_return_to_normal = False

        overlay_text = ""

        if session["finished"]:
            if self.state == "preview":
                overlay_text = "Thank You!"

                if not self.scheduled_return_to_normal:
                    self.scheduled_return_to_normal = True
                    Clock.schedule_once(end_state, 5)

        elif session["started"]:
            if not self.state == "preview":
                self.change_state("preview")

            if session["idle"]:
                overlay_text = "get ready!"
            else:
                timer_value = session["timer_value"]

                if timer_value <= 2:
                    overlay_text = "look at camera!"
                else:
                    overlay_text = str(timer_value)

        if not self.overlay_text == overlay_text:
            self.overlay_text = overlay_text

            if len(overlay_text) > 3:
                if not self.countdown_label.font_size == 150:
                    self.countdown_label.font_size = 150
            else:
                if not self.countdown_label.font_size == 370:
                    self.countdown_label.font_size = 370

            self.countdown_label.text = overlay_text

    def on_image_touch(self, widget, touch):
        """ called when any image is touched
        """
        # ignore all touches during preview!
        if self.state == "preview":
            return True

        if widget.collide_point(touch.x, touch.y):
            # hide the focus widget
            if self.scrollview_hidden:
                self.change_state("normal", widget=widget)

            # show the focus widget
            elif self.focus_widget is not widget:
                self.change_state("focus", widget=widget)

    def handle_new_images_response(self, req, results):
        images = set(results["files"])
        new = natsorted(images - self.loaded)

        if new:
            self.loaded.update(new)

            # retrieve small images, not large
            to_get = list()
            for url in new:
                new_url = url + "?size=small"
                to_get.append(new_url)

            # to_get.reverse()

            self.fetch_images(to_get)

    def get_images(self):
        if self.remote_server is None:
            return

        url = "{protocol}://{host}:{port}/files".format(**self.remote_server)
        UrlRequest(url, self.handle_new_images_response)

    def fetch_images(self, new):
        for filename in new:
            widget = Factory.AsyncImage(source=filename, allow_stretch=True)
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
            Animation(scroll_x=1, t="out_quad", duration=1).start(self.scrollview)

    def unlock(self, dt=None):
        self.locked = False

    def new_focus_widget(self, source):
        # the focus widget is the large preview image that is shown if the user
        # touches a small widget on the screen
        widget = Factory.AsyncImage(source=source)
        widget.allow_stretch = True
        widget.pos_hint = {"top": -1, "center_x": 0.75}
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

        transition = (self.state, state)

        logger.debug("transitioning state %s", transition)

        # TODO: make programmable? save somewhere? idk.
        transitions = {
            ("normal", "focus"): self.transition_normal_focus,
            ("normal", "preview"): self.transition_normal_preview,
            ("normal", "adjustment"): self.transition_normal_adjustment,
            ("focus", "normal"): self.transition_focus_normal,
            ("preview", "normal"): self.transition_preview_normal,
            ("adjustment", "normal"): self.transition_adjustment_normal,
        }

        try:
            next_state = transitions[transition]
        except KeyError:
            logger.critical("invalid state transitioning to: {}".format(state))
            raise RuntimeError
        else:
            self.state = state
            self.stop_running_animations()
            next_state(**kwargs)

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
        ani = Animation(opacity=0.0, duration=0.3)
        # ani.bind(on_complete=self._remove_widget_after_ani)
        self.start_and_log(ani, self.preview_label)
        if self.controls:
            self.start_and_log(ani, self.controls)

        # set the background to normal
        ani = Animation(size_hint=(3, 1.5), t="in_out_quad", duration=0.5)
        self.start_and_log(ani, self.background)

        # show the scrollview and drawer
        ani = Animation(y=0, t="in_out_quad", opacity=1.0, duration=0.5)
        self.start_and_log(ani, search(self, "scrollview_area"))
        self.start_and_log(ani, self.drawer)

        # hide the focus widget
        ani = Animation(
            pos_hint={"top": 0},
            height=screen_height * 0.25,
            t="in_out_quad",
            duration=0.5,
        )
        ani &= Animation(opacity=0.0, duration=0.5)
        self.start_and_log(ani, self.focus_widget)

        # schedule a unlock
        self.locked = True
        Clock.schedule_once(self.unlock, 0.5)

    def transition_normal_focus(self, *args, **kwargs):
        # =====================================================================
        #  N O R M A L  =>  F O C U S
        widget = kwargs["widget"]
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
        self.controls.size_hint = 0.40, 1
        self.controls.opacity = 0

        # animate showing the controls
        ani = Animation(opacity=1.0, duration=0.3)
        self.start_and_log(ani, self.preview_label)
        self.start_and_log(ani, self.controls)

        self.preview_label.pos_hint = {"x": 0.25, "y": 0.47}
        self.add_widget(self.controls)

        # hide the scrollview and drawer
        ani = Animation(x=0, y=-1000, t="in_out_quad", opacity=0.0, duration=0.7)
        self.start_and_log(ani, search(self, "scrollview_area"))
        self.start_and_log(ani, self.drawer)

        # start a simple animation on the background
        x = self.background.pos_hint["x"]
        ani = Animation(t="in_out_quad", size_hint=(4, 2), duration=0.5)
        ani += Animation(pos_hint={"x": x + 1.5}, duration=480)
        self.start_and_log(ani, self.background)

        # show the focus widget
        ani = Animation(
            opacity=1.0,
            pos_hint={"top": 1, "center_x": 0.75},
            size_hint=(1, 1),
            t="in_out_quad",
            duration=0.5,
        )
        ani &= Animation(opacity=1.0, duration=0.5)
        self.start_and_log(ani, self.focus_widget)

        # schedule a unlock
        self.locked = True
        Clock.schedule_once(self.unlock, 0.5)

    def transition_normal_preview(self, *arkg, **kwargs):
        # ====================================================================
        #  N O R M A L  =>  P R E V I E W
        self.scrollview_hidden = True

        self.preview_handler = PreviewHandler()
        self.preview_handler.start()

        # schedule an interval to update the preview widget
        Clock.schedule_interval(self.update_preview, 1 / 120.0)

        self.update_preview()
        self.preview_widget.pos_hint = {"center_x": 0.5, "center_y": 0.5}
        self.preview_widget.size_hint = 0.95, 1

        # make sure countdown text is on top
        self.remove_widget(self.countdown_label)
        self.add_widget(self.countdown_label)

        # hide the scrollview and drawer
        ani = Animation(x=0, y=-1000, t="in_out_quad", opacity=0.0, duration=0.7)
        self.start_and_log(ani, search(self, "scrollview_area"))
        self.start_and_log(ani, self.drawer)

        # start a simple animation on the background
        x = self.background.pos_hint["x"]
        ani = Animation(t="in_out_quad", size_hint=(4, 2), duration=0.5)
        ani += Animation(pos_hint={"x": x + 1.5}, duration=480)
        self.start_and_log(ani, self.background)

        # schedule a unlock
        self.locked = True
        Clock.schedule_once(self.unlock, 0.5)

    def transition_preview_normal(self, *args, **kwargs):
        # ====================================================================
        #  P R E V I E W  =>  N O R M A L
        self.scrollview_hidden = False

        self.preview_widget.pos_hint = {"y": 1}

        # set the background to normal
        ani = Animation(size_hint=(3, 1.5), t="in_out_quad", duration=0.5)
        self.start_and_log(ani, self.background)

        # show the scrollview and drawer
        ani = Animation(y=0, t="in_out_quad", opacity=1.0, duration=0.5)
        self.start_and_log(ani, search(self, "scrollview_area"))
        self.start_and_log(ani, self.drawer)

        # schedule a unlock
        self.locked = True
        Clock.schedule_once(self.unlock, 0.5)

        # unschedule the preview updater
        Clock.unschedule(self.update_preview)

        self.preview_handler.stop()
        self.preview_handler = None

    def transition_normal_adjustment(self, *arkg, **kwargs):
        # ====================================================================
        #  N O R M A L  =>  A D J U S T M E N T
        self.scrollview_hidden = True

        self.preview_handler = PreviewHandler()
        self.preview_handler.start()

        # schedule an interval to update the preview widget
        Clock.schedule_interval(self.update_preview, 1 / 120.0)

        self.update_preview()
        self.preview_widget.pos_hint = {"center_x": 0.5, "center_y": 0.5}
        self.preview_widget.size_hint = 0.95 / 1.5, 1 / 1.5

        # hide the scrollview
        ani = Animation(x=0, y=-1000, t="in_out_quad", opacity=0.0, duration=0.7)
        self.start_and_log(ani, search(self, "scrollview_area"))

        # start a simple animation on the background
        x = self.background.pos_hint["x"]
        ani = Animation(t="in_out_quad", size_hint=(4, 2), duration=0.5)
        ani += Animation(pos_hint={"x": x + 1.5}, duration=480)
        self.start_and_log(ani, self.background)

        # schedule a unlock
        self.locked = True
        Clock.schedule_once(self.unlock, 0.5)

    def transition_adjustment_normal(self, *args, **kwargs):
        # ====================================================================
        #  A D J U S T M E N T  =>  N O R M A L
        self.scrollview_hidden = False
        self.preview_widget.pos_hint = {"y": 1}

        # set the background to normal
        ani = Animation(size_hint=(3, 1.5), t="in_out_quad", duration=0.5)
        self.start_and_log(ani, self.background)

        # show the scrollview
        ani = Animation(y=0, t="in_out_quad", opacity=1.0, duration=0.5)
        self.start_and_log(ani, search(self, "scrollview_area"))

        # schedule a unlock
        self.locked = True
        Clock.schedule_once(self.unlock, 0.5)

        # unschedule the preview updater
        Clock.unschedule(self.update_preview)

        self.preview_handler.stop()
        self.preview_handler = None
