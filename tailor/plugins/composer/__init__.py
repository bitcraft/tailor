"""
image processor/composer that manipulates images
"""

from abc import ABCMeta, abstractmethod

from .renderer import TemplateRenderer


class ComposerFilter(metaclass=ABCMeta):
    @abstractmethod
    def process(self, *args, **kwargs):
        pass


