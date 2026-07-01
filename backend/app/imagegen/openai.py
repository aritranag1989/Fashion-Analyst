import base64

from openai import AsyncOpenAI

from app.config import get_settings
from app.imagegen.base import ConceptShotResult, ImageGenProvider


class OpenAIImageGenProvider(ImageGenProvider):
    """Uses gpt-image-1's images.edit() endpoint (not images.generate()), passing the actual
    rendered tile as the input image with no mask - gpt-image-1 restyles the whole image from the
    prompt when no mask is given, so the concept shot is genuinely conditioned on the tile's real
    colors/pattern rather than a text description of hex codes.

    dall-e-3 was retired 2026-03-04 and is non-functional - do not revert to it as the default
    model. response_format is not passed: GPT image models always return base64
    (response.data[0].b64_json) - that parameter is dall-e-2-only.
    """

    provider_name = "openai"

    def __init__(self) -> None:
        settings = get_settings()
        self._client = AsyncOpenAI(api_key=settings.openai_api_key)
        self._model = settings.openai_image_model

    async def generate_concept_shot(
        self, tile_image_path: str, pattern_type: str, garment_type: str | None = None
    ) -> ConceptShotResult:
        garment = garment_type or "tailored jacket"
        prompt = (
            f"Show this {pattern_type} woven textile pattern as a photorealistic {garment}, "
            f"professional studio lighting, editorial fashion photography style."
        )
        with open(tile_image_path, "rb") as tile_file:
            response = await self._client.images.edit(
                model=self._model, image=tile_file, prompt=prompt
            )
        if not response.data or not response.data[0].b64_json:
            raise RuntimeError(f"OpenAI image edit returned no image data (model={self._model})")
        image_bytes = base64.b64decode(response.data[0].b64_json)
        return ConceptShotResult(
            image_bytes=image_bytes, provider_name=self.provider_name, prompt_used=prompt
        )
