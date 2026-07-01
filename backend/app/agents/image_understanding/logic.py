"""STUB for Phase 1. Real implementation (Phase 2) should:
1. Download images referenced by app.db.postgres.models.Image rows with ocr_status='not_processed'.
2. Run OCR (e.g. Claude vision or a dedicated OCR model) to read logos/factory/product images.
3. Populate the `images` Qdrant collection (schema already exists - see app/db/qdrant_collections.py)
   with image embeddings + OCR text payload, matching the same payload contract as text_chunks.
4. Update Image.ocr_status to 'processed'.

Kept as a real-shaped-but-inert module (not deleted/mocked away) so upgrading it is a drop-in
swap of this function's body, matching every other agent's folder structure.
"""

from app.agents.image_understanding.schemas import ImageOcrResult


async def process_image(image_id: int) -> ImageOcrResult:
    return ImageOcrResult(image_id=image_id, detected_text="", detected_language=None, is_logo=False)
