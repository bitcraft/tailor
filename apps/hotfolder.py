# -*- coding: utf-8 -*-
import queue
import threading
import subprocess
import os
from tkinter import *

from watchdog.observers import Observer
from watchdog.events import RegexMatchingEventHandler
from pubsub import pub

Q_WAITING = 0
Q_PROCESSING = 1
Q_DELETING = 2
Q_COMPLETE = 3

INPUT = os.path.join('C:\\', 'Users', 'Leif')
OUTPUT = ''
PRINTER = 'Microsoft XPS Document Writer'

rundll32_path = r'c:\windows\system32\rundll32.exe'
rundll32_target = r'c:\Windows\System32\shimgvw.dll,ImageView_PrintTo'

paint_path = r'mspaint'
paint_args = r'/pt'


# PRINT_CMD = 'i_view32 xxx.png /print {path}'


def spool(path):
    args = [rundll32_path, rundll32_target, path, PRINTER]
    # args = [paint_path, paint_args, path]
    subprocess.run(args)


def wants_to_close():
    pub.sendMessage('wants_to_close')


class MonitorApp(Frame):
    def __init__(self, parent):
        Frame.__init__(self, parent)
        self.parent = parent

        self.observers = set()

        self.pack(fill=BOTH, expand=1)
        self.buttons_frame = Frame(self)
        self.buttons_frame.pack(side='bottom', expand=1)

        self.status_label = Label(self.buttons_frame)
        self.status_label["text"] = "Running."
        self.status_label.pack(side='top')

        self.button_quit = Button(self.buttons_frame)
        self.button_quit["text"] = "Quit"
        self.button_quit["command"] = wants_to_close
        self.button_quit.pack(side='left')

        pub.subscribe(self.close, 'close_app')

    def close(self):
        self.parent.quit()


class MyObserver(Observer):
    def __init__(self):
        Observer.__init__(self)
        pub.subscribe(self.on_close, 'wants_to_close')

    def on_close(self):
        self.stop()
        self.join()
        pub.sendMessage('close_app')


class Handler(RegexMatchingEventHandler):
    def __init__(self, *args, **kwargs):
        RegexMatchingEventHandler.__init__(self, *args, **kwargs)

    def on_created(self, event):
        pub.sendMessage('new_file', path=event.src_path)


class FileThingy1(object):
    def __init__(self):
        pub.subscribe(self.queue_file, 'new_file')
        pub.subscribe(self.stop, 'wants_to_close')

        self.thread = None
        self.running = False
        self.queue = queue.Queue()

    def start(self):
        self.running = True
        self.thread = threading.Thread(target=self.process_file)
        self.thread.daemon = True
        self.thread.start()

    def stop(self):
        self.running = False

    def queue_file(self, path=None):
        token = {'path': path, 'status': Q_WAITING}
        self.queue.put(token)

    def process_file(self):
        while self.running:
            try:
                token = self.queue.get()
            except queue.Empty:
                pass
            else:
                token['status'] = Q_PROCESSING
                spool(token['path'])
                token['status'] = Q_DELETING
                # delete file
                token['status'] = Q_COMPLETE
                self.queue.task_done()


def main():
    root = Tk()
    root.geometry('200x100')
    app = MonitorApp(root)
    root.protocol("WM_DELETE_WINDOW", wants_to_close)

    event_handler = Handler(['.*\.png'])
    observer = MyObserver()
    observer.schedule(event_handler, INPUT, recursive=False)
    observer.start()

    f = FileThingy1()
    f.start()

    app.mainloop()


if __name__ == '__main__':
    main()
