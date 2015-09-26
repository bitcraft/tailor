# -*- coding: utf-8 -*-
"""
template widgets are used when user taps and opens a finished photo
from the picker.  the image is shown in detail, and this widget overlays
the rendered image with invisible widgets.

the invisible widgets can be tapped to open images that were used to generate
the composite image from the template.

only one templateimage widget will be open, and it is created when the
copmposite screen is used.
"""
from kivy.uix.relativelayout import RelativeLayout

from tailor.graph import ImagePlaceholderNode


class TemplateWidget(RelativeLayout):
    pass


def build_template_widget_from_template(template):
    """
    :param template: tailor.template.Template
    :return: tialor.uix.template.TemplateWidget
    """
    for child in template.dfs_children():
        if isinstance(child, ImagePlaceholderNode):
            rect = child.determine_rect()
