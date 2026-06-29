import os
from dataclasses import dataclass, field

from dotenv import load_dotenv

load_dotenv()


def _env_bool(name: str, default: bool = False) -> bool:
    return os.getenv(name, str(default)).lower() in ("1", "true", "yes", "on")


def _env_list(name: str, default: str) -> list[str]:
    raw = os.getenv(name, default)
    return [item.strip() for item in raw.split(",") if item.strip()]


@dataclass(frozen=True)
class Settings:
    flask_env: str = field(default_factory=lambda: os.getenv("FLASK_ENV", "production"))
    flask_debug: bool = field(default_factory=lambda: _env_bool("FLASK_DEBUG", False))
    flask_host: str = field(default_factory=lambda: os.getenv("FLASK_HOST", "0.0.0.0"))
    flask_port: int = field(default_factory=lambda: int(os.getenv("FLASK_PORT", "5000")))

    secret_key: str = field(default_factory=lambda: os.getenv("SECRET_KEY", ""))

    api_key: str = field(default_factory=lambda: os.getenv("API_KEY", ""))
    cors_origins: list[str] = field(
        default_factory=lambda: _env_list("CORS_ORIGINS", "")
    )

    model_path: str = field(
        default_factory=lambda: os.getenv("MODEL_PATH", "model/speciesv4.pt")
    )
    score_threshold: float = field(
        default_factory=lambda: float(os.getenv("SCORE_THRESHOLD", "0.4"))
    )
    class_names: list[str] = field(
        default_factory=lambda: _env_list(
            "CLASS_NAMES",
            "Ikan Bawal,Ikan Gurame,Ikan Lele,Ikan Nila,Ikan Tuna",
        )
    )

    max_upload_size_mb: int = field(
        default_factory=lambda: int(os.getenv("MAX_UPLOAD_SIZE_MB", "10"))
    )
    allowed_extensions: set[str] = field(
        default_factory=lambda: {
            ext.lower().lstrip(".")
            for ext in _env_list("ALLOWED_EXTENSIONS", "jpg,jpeg,png,webp")
        }
    )

    rate_limit: str = field(
        default_factory=lambda: os.getenv("RATE_LIMIT", "30 per minute")
    )
    rate_limit_storage_uri: str = field(
        default_factory=lambda: os.getenv("RATE_LIMIT_STORAGE_URI", "memory://")
    )

    gunicorn_workers: int = field(
        default_factory=lambda: int(os.getenv("GUNICORN_WORKERS", "2"))
    )
    gunicorn_threads: int = field(
        default_factory=lambda: int(os.getenv("GUNICORN_THREADS", "2"))
    )
    gunicorn_timeout: int = field(
        default_factory=lambda: int(os.getenv("GUNICORN_TIMEOUT", "120"))
    )

    log_level: str = field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))

    enable_docs: bool = field(default_factory=lambda: _env_bool("ENABLE_DOCS", True))
    api_server_url: str = field(
        default_factory=lambda: os.getenv(
            "API_SERVER_URL", "https://fish-species.ferxcode.my.id"
        )
    )

    @property
    def max_upload_bytes(self) -> int:
        return self.max_upload_size_mb * 1024 * 1024

    @property
    def is_development(self) -> bool:
        return self.flask_env.lower() == "development"

    @property
    def is_production(self) -> bool:
        return self.flask_env.lower() == "production"

    def validate(self) -> None:
        if self.is_production and not self.secret_key:
            raise ValueError("SECRET_KEY must be set in production")
        if self.is_production and not self.api_key:
            raise ValueError("API_KEY must be set in production")


settings = Settings()
