# -*- coding: utf-8 -*-
# !/usr/bin/python3

from flask_cors import CORS

from leaf import create_app, Config
import logging

app = create_app()
CORS(app, origins=Config.CORS_ALLOWED_ORIGINS)

if __name__ == "__main__":

    gunicorn_logger = logging.getLogger('gunicorn.error')
    app.logger.handlers = gunicorn_logger.handlers
    app.logger.setLevel(gunicorn_logger.level)

    app.run()
