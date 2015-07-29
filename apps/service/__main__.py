import logging

logger = logging.getLogger()

from argparse import ArgumentParser


def main():
    from service import ServiceApp

    parser = ArgumentParser(prog="tailor", description="tailor camera service")
    args = parser.parse_args()

    app = ServiceApp()
    app.run()


if __name__ == "__main__":
    import sys
    import os

    # hack to allow tailor to run without installing
    sys.path.append(os.path.normpath(
        os.path.join(os.path.dirname(__file__), '..', '..')))

    main()
