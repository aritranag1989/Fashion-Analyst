from urllib.parse import urlparse

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crawlers.playwright_crawler import crawl_page
from app.db.postgres.models import Document, Source
from app.graph.state import RawPage
from app.logging_conf import get_logger

logger = get_logger(__name__)


async def get_or_create_source(
    session: AsyncSession, url: str, source_type: str, name: str | None = None
) -> Source:
    domain = urlparse(url).netloc
    result = await session.execute(select(Source).where(Source.base_url.contains(domain)))
    source = result.scalar_one_or_none()
    if source is not None:
        return source

    source = Source(
        source_type=source_type,
        name=name or domain,
        base_url=url,
    )
    session.add(source)
    await session.flush()
    return source


async def crawl_and_record(session: AsyncSession, url: str, source_type: str) -> RawPage | None:
    page = await crawl_page(url)
    if page is None:
        return None  # disallowed by robots.txt

    source = await get_or_create_source(session, url, source_type)

    document = Document(
        source_id=source.id,
        url=page.url,
        document_type="html",
        content_hash=page.content_hash,
        status="crawled",
    )
    session.add(document)
    await session.flush()

    pdf_links = [link for link in page.linked_urls if link.lower().endswith(".pdf")]

    logger.info("recorded_document", url=page.url, document_id=document.id, pdf_links=len(pdf_links))
    return RawPage(
        url=page.url,
        source_id=source.id,
        document_id=document.id,
        document_type="html",
        content_hash=page.content_hash,
        html=page.html,
        pdf_bytes=None,
        linked_pdf_urls=pdf_links,
    )
