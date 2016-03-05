# -*- coding: utf-8 -*-
from itertools import repeat

__all__ = [
    'timing_generator',
]


def timing_generator(interval, amount, initial=None):
    """ Generator to make generic repeating timer

    Returns (bool, value) tuples, where:
            bool: if true, then this is last iteration of sequence
            value: ether interval or initial value

    :param interval: number to be returned each iteration
    :param amount:  number of iterations
    :param initial: if specified, this value will be used on 1st iteration
    :return: (bool, int)
    """
    assert (amount > 0)

    if initial is not None:
        amount -= 1
        yield amount == 0, initial

    for index, value in enumerate(repeat(interval, amount), start=1):
        yield index == amount, value
