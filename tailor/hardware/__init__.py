"""
Hardware abstractions for the photobooth
"""
def build_interface(spec):
    pass


class Interface:
    pass


class GPIO:
    pass


class Booth:
    """
    implements the hardware interface to booth electronics
    """

    def enable_relay(self, index):
        pass

    def disable_relay(self, index):
        pass

    def set_camera_tilt(self, value):
        pass


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