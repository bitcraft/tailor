def main():
    import logging
    from tailor.apps.monitor import monitor

    logging.basicConfig(level=logging.DEBUG)

    app = monitor.MonitorApp()
    app.run()


if __name__ == "__main__":
    main()
