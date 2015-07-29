def main():
    import logging
    from tailor.apps.server import server

    logging.basicConfig(level=logging.DEBUG)

    app = server.ServerApp()
    app.run(debug=True)


if __name__ == "__main__":
    main()
