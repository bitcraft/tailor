"""
Kivy based app for displaying content to photobooth users

* consumes jpg image frames from the service
* shows user the camera preview
"""
from kivy.app import App
from kivy.uix.widget import Widget


class MonitorWidget(Widget):
    pass


class MonitorApp(App):
    def build(self):
        return MonitorWidget()
