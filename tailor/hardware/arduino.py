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
