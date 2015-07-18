def main():
    import logging
    from tailor.apps.kiosk import kiosk

    logging.basicConfig(level=logging.DEBUG)

    app = kiosk.KioskApp()
    app.run()


if __name__ == "__main__":
    main()
