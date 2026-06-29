from functools import wraps

from flask import jsonify, request

from config.settings import settings


def require_api_key(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not settings.api_key:
            return view(*args, **kwargs)

        provided = request.headers.get("X-API-Key")
        if not provided or provided != settings.api_key:
            return jsonify({"success": False, "message": "Unauthorized"}), 401

        return view(*args, **kwargs)

    return wrapped
