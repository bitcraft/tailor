#!/usr/bin/python
"""
Read a MagTek USB HID Swipe Reader in Linux. A description of this
code can be found at: http://www.micahcarrick.com/credit-card-reader-pyusb.html

You must be using the new PyUSB 1.0 branch and not the 0.x branch.

Copyright (c) 2010 - Micah Carrick
"""
import sys
import time

import usb.core
import usb.util




# keycode mapping
key_pages = [
    '', '', '', '',
    'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm',
    'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z',
    '1', '2', '3', '4', '5', '6', '7', '8', '9', '0', '\n', '^]', '^H',
    '^I', ' ', '-', '=', '[', ']', '\\', '>', ';', "'", '`', ',', '.',
    '/', 'CapsLock', 'F1', 'F2', 'F3', 'F4', 'F5', 'F6', 'F7', 'F8', 'F9',
    'F10', 'F11', 'F12',
    'PS', 'SL', 'Pause', 'Ins', 'Home', 'PU', '^D', 'End', 'PD', '->', '<-',
    '-v', '-^', 'NL',
    'KP/', 'KP*', 'KP-', 'KP+', 'KPE', 'KP1', 'KP2', 'KP3', 'KP4', 'KP5', 'KP6',
    'KP7', 'KP8',
    'KP9', 'KP0', '\\', 'App', 'Pow', 'KP=', 'F13', 'F14']

key_pages_shift = [
    '', '', '', '',
    'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M',
    'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z',
    '!', '@', '#', '$', '%', '^', '&', '*', '(', ')', '\n', '^]', '^H',
    '^I', ' ', '_', '+', '{', '}', '|', '<', ':', '"', '~', '<', '>',
    '?', 'CapsLock', 'F1', 'F2', 'F3', 'F4', 'F5', 'F6', 'F7', 'F8', 'F9',
    'F10', 'F11', 'F12',
    'PS', 'SL', 'Pause', 'Ins', 'Home', 'PU', '^D', 'End', 'PD', '->', '<-',
    '-v', '-^', 'NL',
    'KP/', 'KP*', 'KP-', 'KP+', 'KPE', 'KP1', 'KP2', 'KP3', 'KP4', 'KP5', 'KP6',
    'KP7', 'KP8',
    'KP9', 'KP0', '|', 'App', 'Pow', 'KP=', 'F13', 'F14']

map_keys = lambda c: key_pages_shift[c[1]] if c[0] is 2 else key_pages[c[1]]

VENDOR_ID = 0x1667
PRODUCT_ID = 0x0003


def chunks(l, n):
    """ Yield successive n-sized chunks from l.
    """
    for i in xrange(0, len(l), n):
        yield l[i:i + n]


def map_character(c):
    return key_pages[c]


class GigaTekReader:
    def __init__(self, card_type=None):
        if card_type == None:
            self._expected_length = 167
        elif card_type == 'starbucks':
            self._expected_length = 131
        else:
            raise ValueError

        self.init_reader()

    def init_reader(self):
        device = usb.core.find(idVendor=VENDOR_ID, idProduct=PRODUCT_ID)

        if device is None:
            sys.exit("Could not find GigaTek USB HID Swipe Reader.")

        # make sure the hiddev kernel driver is not active
        if device.is_kernel_driver_active(1):
            try:
                device.detach_kernel_driver(1)
            except usb.core.USBError as e:
                sys.exit("Could not detatch kernel driver: %s" % str(e))

        # set configuration
        try:
            device.set_configuration()
            device.reset()
        except usb.core.USBError as e:
            sys.exit("Could not set configuration: %s" % str(e))

        self._device = device
        self._endpoint = self._device[0][(0, 0)][0]

    def _read_device(self):
        while 1:
            packet = self._device.read(
                self._endpoint.bEndpointAddress,
                self._endpoint.wMaxPacketSize)
            if list(packet) == [0, 0, 0, 0, 0, 0, 0, 0]:
                continue
            yield packet

    def _clear(self):
        time.sleep(1)
        try:
            packet = True
            while packet:
                packet = self._device.read(
                    self._endpoint.bEndpointAddress,
                    self._endpoint.wMaxPacketSize)
        except:
            pass

    def read_swipe(self, callback=None):

        data = []
        swiped = False

        for packet in self._read_device():
            if not data and not map_keys((packet[0], packet[2])) == '%':
                continue

            data += packet
            if len(data) / 8 == self._expected_length:
                break

        this_data = "".join(
            map(map_keys, [(d[0], d[2]) for d in chunks(data, 8)]))

        return this_data


if __name__ == '__main__':
    r = GigaTekReader('starbucks')
    while 1:
        print
        r.read_swipe()
