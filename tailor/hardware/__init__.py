"""
Hardware abstractions for the photobooth
"""
import pyfirmata
import asyncio
import mock

delay = 10 / 1000.

board = None
pin = None


def trigger_firmata_check():
    global board, pin

    loop = asyncio.get_event_loop()
    loop.call_later(delay, check_firmata_inputs)

    # setup firmata
    #board = pyfirmata.Arduino('/dev/tty.usbserial-A6008rIF')
    board = mock.MagicMock(spec=pyfirmata.Arduino)
    pin = board.get_pin('d:i:7')  # digital, input, pin #7


def check_firmata_inputs():
    trigger_firmata_check()
    # value = pin.read()

    # check for session trigger
    value = 0
    if value:
        pass


# new functionality: WAIT FOR PIN
# instead of explicitly polling, use asyncio and wai for input from firmata
@asyncio.coroutine
def wait_for_trigger():
    import time
    end = time.time() + 5
    while time.time() < end:
        yield
    return 1


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


class Relay:
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
