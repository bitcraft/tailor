# -*- coding: utf-8; -*-

from argparse import ArgumentParser
import logging

logger = logging.getLogger("tailor.apps.service.__main__")

from tailor.apps.service import service


if __name__ == "__main__":
    parser = ArgumentParser(prog="tailor", description="tailor camera service")
    args = parser.parse_args()

    app = service.ServiceApp()
    app.run()
