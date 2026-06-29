import logging
from io import BytesIO

from PIL import Image, UnidentifiedImageError
from werkzeug.datastructures import FileStorage

logger = logging.getLogger(__name__)

ALLOWED_MIME_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
}


def _extension(filename: str) -> str:
    if "." not in filename:
        return ""
    return filename.rsplit(".", 1)[-1].lower()


def validate_image_upload(
    file: FileStorage,
    *,
    allowed_extensions: set[str],
    max_bytes: int,
) -> tuple[bytes | None, str | None]:
    if not file or not file.filename:
        return None, "No selected file"

    extension = _extension(file.filename)
    if extension not in allowed_extensions:
        return None, "File type not allowed"

    raw = file.read(max_bytes + 1)
    file.seek(0)

    if not raw:
        return None, "Empty file"

    if len(raw) > max_bytes:
        return None, f"File exceeds maximum size of {max_bytes // (1024 * 1024)} MB"

    try:
        with Image.open(BytesIO(raw)) as img:
            img.verify()
    except (UnidentifiedImageError, OSError) as exc:
        logger.warning("Invalid image upload rejected: %s", exc)
        return None, "Invalid or corrupted image file"

    try:
        with Image.open(BytesIO(raw)) as img:
            img.load()
            if img.format not in {"JPEG", "PNG", "WEBP"}:
                return None, "Image format not supported"
    except (UnidentifiedImageError, OSError) as exc:
        logger.warning("Image load failed after verify: %s", exc)
        return None, "Invalid or corrupted image file"

    return raw, None
