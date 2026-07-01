import httpx
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from app.crawlers.robots import CRAWLER_USER_AGENT, guard
from app.db.postgres.models import Document
from app.extraction.html_parser import extract_html
from app.extraction.pdf_parser import extract_pdf
from app.graph.state import CrawledDocument, RawPage
from app.logging_conf import get_logger

logger = get_logger(__name__)


async def extract_raw_page(session: AsyncSession, page: RawPage) -> CrawledDocument:
    parsed = extract_html(page["html"] or "", page["url"])

    await session.execute(
        update(Document)
        .where(Document.id == page["document_id"])
        .values(status="extracted", language=parsed.language)
    )

    return CrawledDocument(
        url=page["url"],
        source_id=page["source_id"],
        document_id=page["document_id"],
        document_type="html",
        content_hash=page["content_hash"],
        text=parsed.text,
        tables=[],
        language=parsed.language,
    )


async def extract_linked_pdf(
    session: AsyncSession, pdf_url: str, source_id: int
) -> CrawledDocument | None:
    if not await guard(pdf_url):
        return None

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(pdf_url, headers={"User-Agent": CRAWLER_USER_AGENT})
    if response.status_code != 200:
        return None

    extracted = extract_pdf(response.content)

    document = Document(
        source_id=source_id,
        url=pdf_url,
        document_type="pdf",
        status="extracted",
    )
    session.add(document)
    await session.flush()

    logger.info("extracted_pdf", url=pdf_url, document_id=document.id, pages=extracted.page_count)
    return CrawledDocument(
        url=pdf_url,
        source_id=source_id,
        document_id=document.id,
        document_type="pdf",
        content_hash="",
        text=extracted.text,
        tables=extracted.tables,
        language=None,
    )
