from abc import ABC, abstractmethod

from pydantic import BaseModel


class ConceptShotResult(BaseModel):
    image_bytes: bytes
    provider_name: str
    prompt_used: str


class ImageGenProvider(ABC):
    """Swappable AI concept-shot backend. Default is OpenAI's current image model (see
    app.imagegen.openai) - swapping providers changes only which subclass is instantiated (see
    app/imagegen/__init__.py), same shape as app.trade's TradeDataProvider."""

    provider_name: str

    @abstractmethod
    async def generate_concept_shot(
        self, tile_image_path: str, pattern_type: str, garment_type: str | None = None
    ) -> ConceptShotResult:
        """Generate a photorealistic 'on a garment' concept image from a rendered pattern tile."""
