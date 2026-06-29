import logging
from io import BytesIO

import numpy as np
from PIL import Image

from config.settings import settings
from model.model_loader import get_model

logger = logging.getLogger(__name__)

SUPPORTED_IMAGE_FORMATS = {"JPEG", "PNG", "WEBP"}


def predict_image(image, score_threshold: float | None = None) -> list[dict]:
    threshold = score_threshold if score_threshold is not None else settings.score_threshold
    class_names = settings.class_names
    model = get_model()

    raw = image.read()
    image.seek(0)

    with Image.open(BytesIO(raw)) as img:
        if img.mode not in ("RGB", "RGBA", "L"):
            img = img.convert("RGB")
        if img.format and img.format not in SUPPORTED_IMAGE_FORMATS:
            raise ValueError("Unsupported image format")
        img_array = np.array(img)

    results = model(img_array)

    boxes = results[0].boxes
    if boxes is None or len(boxes) == 0:
        return []

    predictions = boxes.xywh.cpu().numpy()
    confidences = boxes.conf.cpu().numpy()
    classes = boxes.cls.cpu().numpy()

    predictions_dict = []

    for prediction, confidence, class_id in zip(predictions, confidences, classes):
        class_id = int(class_id)

        if confidence <= threshold:
            continue

        if not (0 <= class_id < len(class_names)):
            logger.warning("Invalid class_id %s received", class_id)
            continue

        predictions_dict.append(
            {
                "center_x": float(prediction[0]),
                "center_y": float(prediction[1]),
                "width": float(prediction[2]),
                "height": float(prediction[3]),
                "confidence": float(confidence),
                "class_name": class_names[class_id],
            }
        )

    return predictions_dict
