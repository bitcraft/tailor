# import asyncio
#
# from pymata_aio.pymata_core import PymataCore
# from pymata_aio.constants import Constants
#
#
# @asyncio.coroutine
# def wait_for_trigger():
#     board = PymataCore(com_port='/dev/cu.usbmodem641')
#     yield from board.start()
#
#     yield from board.set_pin_mode(6, Constants.OUTPUT, )
#     yield from board.set_pin_mode(7, Constants.OUTPUT, )
#     yield from board.set_pin_mode(2, Constants.INPUT, )
#
#     # set the pin to 128
#     yield from board.digital_write(6, 1)
#     yield from asyncio.sleep(.2)
#     yield from board.digital_write(6, 0)
#     yield from asyncio.sleep(.2)
#     yield from board.digital_write(7, 1)
#     yield from asyncio.sleep(.2)
#     yield from board.digital_write(7, 0)
#     yield from asyncio.sleep(.2)
#
#     # shutdown
#     yield from board.shutdown()
