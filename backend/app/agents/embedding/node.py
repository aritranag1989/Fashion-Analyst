from app.agents.embedding.logic import embed_catalog_tables, embed_document
from app.db.postgres.base import AsyncSessionLocal
from app.graph.state import IngestionState
from app.logging_conf import get_logger

logger = get_logger(__name__)


async def embedding_node(state: IngestionState) -> dict:
    """Embeds only documents backing an above-threshold VerificationResult - unverified facts
    never make it into the vector index."""
    documents_by_url = {doc["url"]: doc for doc in state["crawled_documents"]}
    errors: list[str] = []

    async with AsyncSessionLocal() as session:
        for verification in state["verification_results"]:
            for url in verification["corroborating_source_urls"]:
                document = documents_by_url.get(url)
                if document is None:
                    continue
                try:
                    await embed_document(session, document, verification)
                    await embed_catalog_tables(session, document, verification)
                except Exception as exc:  # noqa: BLE001
                    logger.warning("embedding_failed", url=url, error=str(exc))
                    errors.append(f"embedding_failed: {url}: {exc}")
        await session.commit()

    return {"errors": errors}
