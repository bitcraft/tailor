"""
Kivy based app for displaying content to photobooth users

* consumes jpg image frames from the service
* shows user the camera preview
"""
import queue
from kivy.app import App
from kivy.graphics.texture import Texture
from kivy.uix.image import Image
from kivy.uix.widget import Widget


class CameraPreview(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.queue = queue.Queue()

    def update_preview(self, *args, **kwargs):
        try:
            image_data = self.queue.get(False)
        except queue.Empty:
            return

        # textures must be created in the main thread; this is a limitation of the backend
        texture = Texture.create_from_data(image_data)

        image = None
        if image is None:
            image = Image(texture=texture, nocache=True)
            image.allow_stretch = True
            image.size_hint = None, None
            image.size = (1280, 1024)
            image.x = (1280 / 2) - (image.width / 2)
            image.y = -image.height
            self.layout.add_widget(self.preview_widget)
        else:
            image.texture = texture


class MonitorWidget(Widget):
    pass


class MonitorApp(App):
    def build(self):
        return MonitorWidget()
