"""Incremental re-crawl of an already-known Source: re-fetches its base_url and runs it through
extraction -> verification -> embedding -> knowledge_graph, WITHOUT re-running Industry Research
(no need to re-discover a company we already track; that would waste an LLM+web-search call on
every scheduled re-crawl). This is the code path app/tasks/scheduled.py's celery-beat task uses.
"""

from datetime import datetime, timezone

from sqlalchemy import select

from app.agents.document_extraction.logic import extract_raw_page
from app.agents.embedding.logic import embed_catalog_tables, embed_document
from app.agents.knowledge_graph.logic import write_verified_result_to_graph
from app.agents.verification.logic import (
    build_flagged_result,
    extract_fact,
    group_facts_across_documents,
    persist_verified_group,
    score_confidence,
)
from app.agents.website_crawling.logic import crawl_and_record
from app.config import get_settings
from app.db.postgres.base import AsyncSessionLocal
from app.db.postgres.models import Source
from app.kg.neo4j_client import get_neo4j_driver
from app.logging_conf import get_logger

logger = get_logger(__name__)


async def run_recrawl(source_id: int) -> dict:
    settings = get_settings()

    async with AsyncSessionLocal() as session:
        source = await session.get(Source, source_id)
        if source is None:
            return {"skipped": True, "reason": "source_not_found"}

        raw_page = await crawl_and_record(session, source.base_url, source.source_type)
        if raw_page is None:
            return {"skipped": True, "reason": "robots_disallowed"}

        crawled_document = await extract_raw_page(session, raw_page)
        source.last_crawled_at = datetime.now(timezone.utc)
        await session.commit()

    fact = await extract_fact(crawled_document)
    if fact is None:
        return {"verified": 0, "flagged": 0}

    groups = group_facts_across_documents([(fact, crawled_document)])

    async with AsyncSessionLocal() as session:
        driver = get_neo4j_driver()
        verified_count = 0
        flagged_count = 0

        for group in groups:
            confidence = score_confidence(group)
            if confidence >= settings.confidence_threshold:
                verification = await persist_verified_group(session, group, confidence)
                await embed_document(session, crawled_document, verification)
                await embed_catalog_tables(session, crawled_document, verification)
                await write_verified_result_to_graph(driver, verification)
                verified_count += 1
            else:
                build_flagged_result(group, confidence)
                flagged_count += 1

        await session.commit()

    logger.info("recrawl_finished", source_id=source_id, verified=verified_count, flagged=flagged_count)
    return {"verified": verified_count, "flagged": flagged_count}
