from flask import Response, jsonify
from flask_swagger_ui import get_swaggerui_blueprint

from config.settings import settings
from docs.openapi import build_openapi_spec

REDOC_HTML = """<!DOCTYPE html>
<html lang="id">
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Fish Species API - ReDoc</title>
  <style>body { margin: 0; padding: 0; }</style>
</head>
<body>
  <redoc spec-url="/openapi.json"></redoc>
  <script src="https://cdn.jsdelivr.net/npm/redoc@2.4.0/bundles/redoc.standalone.js"></script>
</body>
</html>
"""


def register_docs(app) -> None:
    @app.route("/openapi.json", methods=["GET"])
    def openapi_json():
        return jsonify(build_openapi_spec(settings.api_server_url))

    @app.route("/redoc", methods=["GET"])
    def redoc():
        return Response(REDOC_HTML, mimetype="text/html")

    swagger_ui = get_swaggerui_blueprint(
        "/docs",
        "/openapi.json",
        config={
            "app_name": "Fish Species API",
            "displayRequestDuration": True,
            "docExpansion": "list",
            "filter": True,
            "tryItOutEnabled": True,
        },
    )
    app.register_blueprint(swagger_ui)
