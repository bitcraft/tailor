from threading import Thread
from Queue import Queue, Empty
import time
import sys


ON_POSIX = 'posix' in sys.builtin_module_names


def enqueue_output(out, queue):
    while 1:
        byte = out.read(1)
        queue.put(byte)
    out.close()


key = None


def handle_data(data):
    global key
    if key is None:
        key = data
        print
        'got key!'
    else:
        if key == data:
            print
            'match!'
        else:
            print
            'mismatch!'


if __name__ == '__main__':
    device = '/dev/input/by-id/usb-GIGATEK_PROMAG_Programmable_Keyboard-event-kbd'
    # /dev/input/by-id/usb-GIGATEK_PROMAG_Programmable_Keyboard-event-if01

    #p = Popen(['myprogram.exe'], stdout=PIPE, bufsize=1, close_fds=ON_POSIX)
    reader = open(device)
    q = Queue()
    t = Thread(target=enqueue_output, args=(reader, q))
    t.daemon = True  # thread dies with the program
    t.start()

    swipe_time = None
    temp = ''

    while 1:
        try:
            byte = q.get_nowait()
        except Empty:
            if swipe_time is None:
                pass
            elif time.time() > swipe_time + 1:
                handle_data(temp)
                temp = ''
                swipe_time = None
        else:
            swipe_time = time.time()
            temp += byte
