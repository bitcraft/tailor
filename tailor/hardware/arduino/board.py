# -*- coding: utf-8 -*-
import asyncio

from .protocol.factory import build, parse


class Board:
    def __init__(self, serial_device=None, wait=2):
        """ Exposes the Firmata API

        :param serial_device: Serial device to use, or None
        :param wait: Time to wait for board to reset.  Uno=2, Leo=0
        """
        self.serial_device = serial_device
        self.sleep_time_until_ready = wait
        self.digital_pin_ports = [0] * 8  # move to autoconfig
        self.started = False

        self.packet_parser = parse(self.handle_packet)
        self.packet_parser.send(None)
        self.packet_factory = build

        # this is incorrect, needs to be future/cb, but i'm out of time
        # polling for now~
        self.loop = asyncio.get_event_loop()
        self.loop.call_later(0.1, self.check_input())
        self._awaited_future = None

    def start(self):
        if self.started:
            raise RuntimeError

        yield from asyncio.sleep(self.sleep_time_until_ready)
        self.started = True

    def check_input(self):
        self.loop.call_later(0.1, self.check_input)
        for byte in self.serial_device.read():
            self.packet_parser.send(byte)

    def handle_packet(self, packet):
        # TODO: check for waiting types
        if self._awaited_future:
            self._awaited_future.set_result(packet)
            self._awaited_future = None

    def send_packet(self, name, **kwargs):
        packet = self.packet_factory(name, **kwargs)
        self.send_bytes(packet)

    def send_bytes(self, command):
        command = bytes(command)
        self.serial_device.write(command)

    def wait_for_packet(self):
        self._awaited_future = asyncio.Future()
        return self._awaited_future
