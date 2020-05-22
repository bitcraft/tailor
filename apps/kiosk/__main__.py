# -*- coding: utf-8 -*-
import logging

logging.basicConfig(level=logging.DEBUG)


def main():
    from kiosk import new

    app = new()
    app.run()


if __name__ == "__main__":
    import sys
    import os

    # hack to allow tailor to run without installing
    sys.path.append(
        os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ".."))
    )

    main()
