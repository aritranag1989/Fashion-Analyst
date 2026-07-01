from abc import ABC, abstractmethod


class EmbeddingProvider(ABC):
    """Swappable embedding backend. Default is Voyage AI; OpenAI is the alternative.

    Swapping providers changes only which subclass is instantiated (see
    app/rag/embeddings/__init__.py) - Qdrant collection schema is unaffected as long as
    `dimension` matches settings.embedding_dim (a dimension change requires a reindex).
    """

    model_name: str
    dimension: int

    @abstractmethod
    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Embed a batch of text chunks, returned in the same order."""

    async def embed_query(self, query: str) -> list[float]:
        return (await self.embed_texts([query]))[0]
