from qdrant_client import AsyncQdrantClient
from qdrant_client.models import Distance, PayloadSchemaType, VectorParams

from app.config import get_settings
from app.db.qdrant_client import (
    IMAGES_COLLECTION,
    PRODUCT_CATALOG_CHUNKS_COLLECTION,
    TEXT_CHUNKS_COLLECTION,
)

# Payload fields stored alongside every point (see docs/architecture.md for the full contract):
# document_id, company_id, product_id, source_url, source_type, chunk_text, chunk_index,
# language, crawled_at, confidence_score, entity_tags.
PAYLOAD_INDEXES = {
    "company_id": PayloadSchemaType.INTEGER,
    "source_type": PayloadSchemaType.KEYWORD,
    "language": PayloadSchemaType.KEYWORD,
    "confidence_score": PayloadSchemaType.FLOAT,
}

COLLECTIONS = [TEXT_CHUNKS_COLLECTION, PRODUCT_CATALOG_CHUNKS_COLLECTION, IMAGES_COLLECTION]


async def ensure_collections(client: AsyncQdrantClient) -> None:
    settings = get_settings()
    existing = {c.name for c in (await client.get_collections()).collections}

    for name in COLLECTIONS:
        if name not in existing:
            await client.create_collection(
                collection_name=name,
                vectors_config=VectorParams(size=settings.embedding_dim, distance=Distance.COSINE),
            )
        for field, schema in PAYLOAD_INDEXES.items():
            await client.create_payload_index(
                collection_name=name, field_name=field, field_schema=schema
            )
