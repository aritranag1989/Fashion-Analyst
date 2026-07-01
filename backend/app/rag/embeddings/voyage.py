import voyageai

from app.config import get_settings
from app.rag.embeddings.base import EmbeddingProvider


class VoyageEmbeddingProvider(EmbeddingProvider):
    def __init__(self) -> None:
        settings = get_settings()
        self.model_name = settings.voyage_embedding_model
        self.dimension = settings.embedding_dim
        self._client = voyageai.AsyncClient(api_key=settings.voyage_api_key)

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        result = await self._client.embed(
            texts, model=self.model_name, output_dimension=self.dimension
        )
        return result.embeddings

    async def embed_query(self, query: str) -> list[float]:
        result = await self._client.embed(
            [query], model=self.model_name, input_type="query", output_dimension=self.dimension
        )
        return result.embeddings[0]
