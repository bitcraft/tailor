"""
Hardware abstractions for the photobooth
"""
import pyfirmata


class Booth:
    """
    implements the hardware interface to booth electronics
    """
    def __init__(self):
        main_light = Relay(0)
        session_light = Relay(1)

        self.relays = [main_light, session_light]
        self.triggers = []
        self.lights = [main_light, session_light]


class Relay(object):
    def __init__(self, arduino, index, normal_state=0):
        self._arduino = arduino
        self._index = index
        self._normal_state = bool(normal_state)
        self._state = self._normal_state

    def _set_state(self, value):
        self._state = 1 if bool(value) else 0
        self._arduino.sendCommand(self._index, self._state)

    def on(self):
        self._set_state(self._normal_state)

    def off(self):
        self._set_state(not self._normal_state)

    def toggle(self):
        self._set_state(not self._state)
