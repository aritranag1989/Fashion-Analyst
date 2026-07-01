import io
import uuid
from pathlib import Path

from PIL import Image

from app.config import get_settings


def _data_root() -> Path:
    return Path(get_settings().pattern_data_dir)


def save_bytes(content: bytes, subdir: str, extension: str) -> str:
    """Saves bytes under <pattern_data_dir>/<subdir>/<uuid>.<extension>. Returns the path
    relative to pattern_data_dir - what actually gets stored in the DB, so switching storage
    backends later is a change to this function only, not a schema migration."""
    directory = _data_root() / subdir
    directory.mkdir(parents=True, exist_ok=True)
    filename = f"{uuid.uuid4().hex}.{extension}"
    (directory / filename).write_bytes(content)
    return f"{subdir}/{filename}"


def save_image(image: Image.Image, subdir: str, extension: str = "png") -> str:
    buffer = io.BytesIO()
    image.save(buffer, format=extension.upper())
    return save_bytes(buffer.getvalue(), subdir, extension)


def resolve_path(relative_path: str) -> Path:
    return _data_root() / relative_path
