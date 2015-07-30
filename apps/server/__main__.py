import logging

logging.basicConfig(level=logging.DEBUG)


def main():
    from tailor.net import guess_local_ip_addresses
    from server import ServerApp

    addr = guess_local_ip_addresses()

    app = ServerApp()
    app.run(host=addr, debug=True)


if __name__ == "__main__":
    import sys
    import os

    # hack to allow tailor to run without installing
    sys.path.append(os.path.normpath(
        os.path.join(os.path.dirname(__file__), '..', '..')))

    main()
