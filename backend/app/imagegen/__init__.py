from functools import lru_cache

from app.config import get_settings
from app.imagegen.base import ImageGenProvider
from app.imagegen.openai import OpenAIImageGenProvider

# Phase 2: register additional providers here (an image-conditioning-capable alternative, etc.)
_PROVIDERS: dict[str, type[ImageGenProvider]] = {
    "openai": OpenAIImageGenProvider,
}


@lru_cache
def get_imagegen_provider() -> ImageGenProvider:
    settings = get_settings()
    return _PROVIDERS[settings.imagegen_provider]()
