from app.agents.website_crawling.logic import crawl_and_record
from app.crawlers.sources.seed_sources import SEED_SOURCES
from app.db.postgres.base import AsyncSessionLocal
from app.graph.state import IngestionState, RawPage
from app.logging_conf import get_logger

logger = get_logger(__name__)


async def website_crawling_node(state: IngestionState) -> dict:
    urls_to_crawl: list[tuple[str, str]] = [
        (seed.base_url, seed.source_type) for seed in SEED_SOURCES
    ]
    urls_to_crawl += [
        (company["website_url"], "website")
        for company in state["discovered_companies"]
        if company.get("website_url")
    ]

    raw_pages: list[RawPage] = []
    errors: list[str] = []

    async with AsyncSessionLocal() as session:
        for url, source_type in urls_to_crawl:
            try:
                page = await crawl_and_record(session, url, source_type)
                if page is not None:
                    raw_pages.append(page)
            except Exception as exc:  # noqa: BLE001 - one bad page must not abort the batch
                logger.warning("crawl_failed", url=url, error=str(exc))
                errors.append(f"crawl_failed: {url}: {exc}")
        await session.commit()

    return {"raw_pages": raw_pages, "errors": errors}
