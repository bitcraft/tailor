def main():
    import logging
    from server import ServerApp

    logging.basicConfig(level=logging.DEBUG)

    app = ServerApp()
    app.run(debug=True)


if __name__ == "__main__":
    import sys
    import os

    # hack to allow tailor to run without installing
    sys.path.append(os.path.normpath(
        os.path.join(os.path.dirname(__file__), '..', '..')))

    main()
