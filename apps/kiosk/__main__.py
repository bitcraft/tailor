def main():
    import logging
    from kiosk import new

    logging.basicConfig(level=logging.DEBUG)

    app = new()
    app.run()


if __name__ == "__main__":
    main()
