import time
import asyncio
from functools import partial


def wait():
    print('work')
    return asyncio.get_event_loop().run_in_executor(None, partial(time.sleep, 5))

begin = time.time()
print('begin')


@asyncio.coroutine
def main():
    yield from asyncio.wait([
        wait(),
        wait(),
        wait(),
        wait(),
    ])

asyncio.get_event_loop().run_until_complete(main())

print('end')
print(time.time() - begin)
