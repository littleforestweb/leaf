# -*- coding: utf-8 -*-
# !/usr/bin/python3

from flask_cors import CORS

from leaf import create_app
from leaf.config import Config

app = create_app()
CORS(app)

# @app.after_request
# def add_header(response):
#     # response.headers["X-Frame-Options"] = "SAMEORIGIN"
#     # # response.headers["Content-Security-Policy"] = "default-src 'self' " + Config.MAIN_SERVER + " " + Config.PREVIEW_SERVER + " leaf.littleforest.co.uk leaf.littleforest.co.uk:8082 www.miningreview.com 'unsafe-inline'; img-src 'self' " + Config.MAIN_SERVER + " " + Config.PREVIEW_SERVER + " leaf.littleforest.co.uk leaf.littleforest.co.uk:8082 www.miningreview.com data: *.w3.org; frame-ancestors 'self'; report-to csp-endpoint"
#     # response.headers["Report-To"] = '{"group": "csp-endpoint","max_age": 10886400,"endpoints": [{"url": "/csp-endpoint"}],"include_subdomains": true}'
#     # response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
#     # response.headers["X-Content-Type-Options"] = "nosniff"
#     # response.headers["Referrer-Policy"] = "no-referrer"
#     # response.headers["X-XSS-Protection"] = "1; mode=block"
#     # response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
#     # response.headers["Pragma"] = "no-cache"
#     # response.headers["Expires"] = "0"
#     # return response


if __name__ == '__main__':
    app.run()
