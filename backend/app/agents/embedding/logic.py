import hashlib
import uuid

from qdrant_client.models import PointStruct
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.postgres.models import EmbeddingMetadata
from app.db.qdrant_client import (
    PRODUCT_CATALOG_CHUNKS_COLLECTION,
    TEXT_CHUNKS_COLLECTION,
    get_qdrant_client,
)
from app.extraction.catalog_parser import flatten_table_to_sentences
from app.graph.state import CrawledDocument, VerificationResult
from app.logging_conf import get_logger
from app.rag.chunking import chunk_text
from app.rag.embeddings import get_embedding_provider

logger = get_logger(__name__)


def _chunk_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


async def embed_document(
    session: AsyncSession, document: CrawledDocument, verification: VerificationResult
) -> int:
    """Chunks + embeds a verified document's prose text into the text_chunks collection.
    Returns the number of chunks written."""
    provider = get_embedding_provider()
    qdrant = get_qdrant_client()

    chunks = chunk_text(document["text"])
    if not chunks:
        return 0

    vectors = await provider.embed_texts(chunks)
    company_id = verification["payload"].get("company_id")

    points = []
    for index, (chunk, vector) in enumerate(zip(chunks, vectors)):
        point_id = str(uuid.uuid4())
        payload = {
            "document_id": document["document_id"],
            "company_id": company_id,
            "source_url": document["url"],
            "source_type": document["document_type"],
            "chunk_text": chunk,
            "chunk_index": index,
            "language": document["language"],
            "confidence_score": verification["confidence"],
            "entity_tags": [verification["entity_type"]],
        }
        points.append(PointStruct(id=point_id, vector=vector, payload=payload))
        session.add(
            EmbeddingMetadata(
                qdrant_point_id=point_id,
                qdrant_collection=TEXT_CHUNKS_COLLECTION,
                source_table="documents",
                source_row_id=document["document_id"],
                document_id=document["document_id"],
                chunk_index=index,
                chunk_text_hash=_chunk_hash(chunk),
                embedding_model=provider.model_name,
                embedding_dim=provider.dimension,
            )
        )

    await qdrant.upsert(collection_name=TEXT_CHUNKS_COLLECTION, points=points)
    logger.info("embedded_document", url=document["url"], chunks=len(points))
    return len(points)


async def embed_catalog_tables(
    session: AsyncSession, document: CrawledDocument, verification: VerificationResult
) -> int:
    """Flattens any extracted catalog/spec tables into sentences and embeds them separately into
    the product_catalog_chunks collection."""
    if not document["tables"]:
        return 0

    provider = get_embedding_provider()
    qdrant = get_qdrant_client()
    company_id = verification["payload"].get("company_id")

    sentences: list[str] = []
    for table in document["tables"]:
        sentences.extend(flatten_table_to_sentences(table))
    if not sentences:
        return 0

    vectors = await provider.embed_texts(sentences)
    points = []
    for index, (sentence, vector) in enumerate(zip(sentences, vectors)):
        point_id = str(uuid.uuid4())
        payload = {
            "document_id": document["document_id"],
            "company_id": company_id,
            "source_url": document["url"],
            "source_type": "catalog_table",
            "chunk_text": sentence,
            "chunk_index": index,
            "language": document["language"],
            "confidence_score": verification["confidence"],
            "entity_tags": ["product"],
        }
        points.append(PointStruct(id=point_id, vector=vector, payload=payload))
        session.add(
            EmbeddingMetadata(
                qdrant_point_id=point_id,
                qdrant_collection=PRODUCT_CATALOG_CHUNKS_COLLECTION,
                source_table="documents",
                source_row_id=document["document_id"],
                document_id=document["document_id"],
                chunk_index=index,
                chunk_text_hash=_chunk_hash(sentence),
                embedding_model=provider.model_name,
                embedding_dim=provider.dimension,
            )
        )

    await qdrant.upsert(collection_name=PRODUCT_CATALOG_CHUNKS_COLLECTION, points=points)
    logger.info("embedded_catalog_tables", url=document["url"], rows=len(points))
    return len(points)
