from app.agents.document_extraction.logic import extract_linked_pdf, extract_raw_page
from app.db.postgres.base import AsyncSessionLocal
from app.graph.state import CrawledDocument, IngestionState
from app.logging_conf import get_logger

logger = get_logger(__name__)

MAX_LINKED_PDFS_PER_PAGE = 3


async def document_extraction_node(state: IngestionState) -> dict:
    crawled_documents: list[CrawledDocument] = []
    errors: list[str] = []

    async with AsyncSessionLocal() as session:
        for page in state["raw_pages"]:
            try:
                crawled_documents.append(await extract_raw_page(session, page))
            except Exception as exc:  # noqa: BLE001
                logger.warning("html_extraction_failed", url=page["url"], error=str(exc))
                errors.append(f"html_extraction_failed: {page['url']}: {exc}")

            for pdf_url in page["linked_pdf_urls"][:MAX_LINKED_PDFS_PER_PAGE]:
                try:
                    pdf_doc = await extract_linked_pdf(session, pdf_url, page["source_id"])
                    if pdf_doc is not None:
                        crawled_documents.append(pdf_doc)
                except Exception as exc:  # noqa: BLE001
                    logger.warning("pdf_extraction_failed", url=pdf_url, error=str(exc))
                    errors.append(f"pdf_extraction_failed: {pdf_url}: {exc}")

        await session.commit()

    return {"crawled_documents": crawled_documents, "errors": errors}
