import logging

from ultralytics import YOLO

from config.settings import settings

logger = logging.getLogger(__name__)

_model = None


def load_model() -> YOLO:
    global _model
    if _model is None:
        logger.info("Loading model from %s", settings.model_path)
        _model = YOLO(settings.model_path)
        _model.eval()
        logger.info("Model loaded successfully")
    return _model


def get_model() -> YOLO:
    return load_model()


def is_model_loaded() -> bool:
    return _model is not None
