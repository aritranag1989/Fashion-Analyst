from functools import lru_cache

from qdrant_client import AsyncQdrantClient

from app.config import get_settings

TEXT_CHUNKS_COLLECTION = "text_chunks"
PRODUCT_CATALOG_CHUNKS_COLLECTION = "product_catalog_chunks"
IMAGES_COLLECTION = "images"


@lru_cache
def get_qdrant_client() -> AsyncQdrantClient:
    settings = get_settings()
    return AsyncQdrantClient(url=settings.qdrant_url, api_key=settings.qdrant_api_key or None)
