import logging

from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from werkzeug.exceptions import RequestEntityTooLarge

from config.settings import settings
from model.model_loader import is_model_loaded, load_model
from routes.predict import predict_image
from utils.auth import require_api_key
from utils.validators import validate_image_upload

logger = logging.getLogger(__name__)

limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=settings.rate_limit_storage_uri,
    default_limits=[],
)


def _configure_logging() -> None:
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )


def create_app() -> Flask:
    settings.validate()

    _configure_logging()

    app = Flask(__name__)
    app.config["SECRET_KEY"] = settings.secret_key or "dev-only-change-me"
    app.config["MAX_CONTENT_LENGTH"] = settings.max_upload_bytes

    if settings.cors_origins:
        CORS(app, resources={r"/*": {"origins": settings.cors_origins}})

    limiter.init_app(app)

    if settings.enable_docs:
        from routes.docs import register_docs

        register_docs(app)
        logger.info("API docs enabled at /docs (Swagger UI) and /redoc")

    @app.after_request
    def set_security_headers(response):
        # Swagger UI / ReDoc membutuhkan inline script & style
        if request.path.startswith("/docs") or request.path == "/redoc":
            response.headers["X-Frame-Options"] = "SAMEORIGIN"
            response.headers["Content-Security-Policy"] = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
                "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
                "img-src 'self' data: https:; "
                "font-src 'self' data: https://cdn.jsdelivr.net; "
                "connect-src 'self'"
            )
        else:
            response.headers["X-Frame-Options"] = "DENY"

        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        if not request.path.startswith("/docs"):
            response.headers["Cache-Control"] = "no-store"
        if settings.is_production and not request.path.startswith("/docs"):
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains"
            )
        return response

    @app.errorhandler(RequestEntityTooLarge)
    def handle_payload_too_large(_error):
        return jsonify(
            {
                "success": False,
                "message": f"File exceeds maximum size of {settings.max_upload_size_mb} MB",
            }
        ), 413

    @app.errorhandler(429)
    def handle_rate_limit(_error):
        return jsonify(
            {"success": False, "message": "Rate limit exceeded. Try again later."}
        ), 429

    @app.errorhandler(500)
    def handle_internal_error(_error):
        logger.exception("Unhandled server error")
        return jsonify({"success": False, "message": "Internal server error"}), 500

    @app.route("/health", methods=["GET"])
    def health():
        return jsonify({"status": "ok"}), 200

    @app.route("/ready", methods=["GET"])
    def ready():
        if not is_model_loaded():
            return jsonify({"status": "not_ready", "model_loaded": False}), 503
        return jsonify({"status": "ready", "model_loaded": True}), 200

    @app.route("/predict", methods=["POST"])
    @limiter.limit(settings.rate_limit)
    @require_api_key
    def predict():
        if "image" not in request.files:
            return jsonify({"success": False, "message": "No image provided"}), 400

        image = request.files["image"]
        _, error = validate_image_upload(
            image,
            allowed_extensions=settings.allowed_extensions,
            max_bytes=settings.max_upload_bytes,
        )
        if error:
            return jsonify({"success": False, "message": error}), 400

        try:
            result = predict_image(image)
            return jsonify({"success": True, "predictions": result})
        except Exception:
            logger.exception("Prediction failed")
            return jsonify({"success": False, "message": "Error processing image"}), 500

    try:
        load_model()
    except Exception:
        logger.exception("Failed to load model at startup")
        if settings.is_production:
            raise

    return app


app = create_app()

if __name__ == "__main__":
    app.run(
        host=settings.flask_host,
        port=settings.flask_port,
        debug=settings.flask_debug,
    )
