from openai import AsyncOpenAI

from app.config import get_settings
from app.rag.embeddings.base import EmbeddingProvider


class OpenAIEmbeddingProvider(EmbeddingProvider):
    def __init__(self) -> None:
        settings = get_settings()
        self.model_name = settings.openai_embedding_model
        self.dimension = settings.embedding_dim
        self._client = AsyncOpenAI(api_key=settings.openai_api_key)

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        response = await self._client.embeddings.create(
            model=self.model_name, input=texts, dimensions=self.dimension
        )
        return [item.embedding for item in response.data]
