from functools import lru_cache

from app.config import get_settings
from app.rag.embeddings.base import EmbeddingProvider


@lru_cache
def get_embedding_provider() -> EmbeddingProvider:
    settings = get_settings()
    if settings.embedding_provider == "openai":
        from app.rag.embeddings.openai import OpenAIEmbeddingProvider

        return OpenAIEmbeddingProvider()

    from app.rag.embeddings.voyage import VoyageEmbeddingProvider

    return VoyageEmbeddingProvider()
