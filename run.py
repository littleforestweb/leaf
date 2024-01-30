# -*- coding: utf-8 -*-
# !/usr/bin/python3

from flask_cors import CORS

from leaf import create_app

app = create_app()
CORS(app)

if __name__ == '__main__':
    app.run()
