def main():
    import logging
    from tailor.apps.service import service

    logging.basicConfig(level=logging.DEBUG)

    app = service.ServiceApp()
    app.run()


if __name__ == "__main__":
    main()
