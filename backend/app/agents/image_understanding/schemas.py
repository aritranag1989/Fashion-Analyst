from pydantic import BaseModel


class ImageOcrResult(BaseModel):
    image_id: int
    detected_text: str
    detected_language: str | None = None
    is_logo: bool = False
