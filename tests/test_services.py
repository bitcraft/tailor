# -*- coding: utf-8 -*-
from unittest import TestCase

from apps.service.async_helpers import timing_generator


class TimingTests(TestCase):
    def test_normal(self):
        exp = [(False, 2), (False, 2), (False, 2), (True, 2)]
        res = list(timing_generator(2, 4))
        self.assertEqual(exp, res)

    def test_with_initial(self):
        exp = [(False, 10), (False, 2), (False, 2), (True, 2)]
        res = list(timing_generator(2, 4, 10))
        self.assertEqual(exp, res)

    def test_normal_len1(self):
        exp = [(True, 2)]
        res = list(timing_generator(2, 1))
        self.assertEqual(exp, res)

    def test_with_initial_len1(self):
        exp = [(True, 10)]
        res = list(timing_generator(2, 1, 10))
        self.assertEqual(exp, res)

    def test_normal_len0(self):
        # TODO: raise error
        exp = []
        res = list(timing_generator(2, 0))
        self.assertEqual(exp, res)

    def test_with_initial_len0(self):
        # TODO: raise error
        exp = []
        res = list(timing_generator(2, 0, 10))
        self.assertEqual(exp, res)
