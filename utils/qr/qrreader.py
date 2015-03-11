#!/usr/bin/env python
import sys


def handle(decode):
    decode = decode.strip()
    print
    decode
    sys.stdout.flush()


if __name__ == '__main__':
    del sys.argv[0]
    if len(sys.argv):
        for decode in sys.argv:
            handle(decode)

    if not sys.stdin.isatty():
        while 1:
            decode = sys.stdin.readline()
            if not decode:
                break
            handle(decode)
