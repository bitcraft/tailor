import queue

from kivy.clock import Clock
from kivy.core.camera import CameraBase

from kivy.graphics.texture import Texture


class TailorStreamingCamera(CameraBase):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.queue = queue.Queue()
        self._format = 'rgb'

    def init_camera(self):
        if not self.stopped:
            self.start()

    def start(self):
        super().start()
        Clock.unschedule(self._update)
        Clock.schedule_interval(self._update, self.fps)

    def stop(self):
        super().stop()
        Clock.unschedule(self._update)

    def _update(self, dt):
        if self.stopped:
            return

        if self._texture is None:
            # Create the texture
            self._texture = Texture.create(self._resolution)
            self._texture.flip_vertical()
            self.dispatch('on_load')
        try:
            self._buffer = self._grab_last_frame()
            self._copy_to_gpu()
        except:
            # Logger.exception('OpenCV: Couldn\'t get image from Camera')
            pass

    def _grab_last_frame(self):
        try:
            image_data = self.queue.get(False)
        except queue.Empty:
            return

        return image_data
