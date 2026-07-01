import asyncio
from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from app.celery_app import celery_app
from app.db.postgres.base import AsyncSessionLocal
from app.db.postgres.models import Source
from app.graph.recrawl import run_recrawl
from app.logging_conf import get_logger

logger = get_logger(__name__)

FREQUENCY_TO_TIMEDELTA = {
    "hourly": timedelta(hours=1),
    "daily": timedelta(days=1),
    "weekly": timedelta(weeks=1),
    "monthly": timedelta(days=30),
}


async def _find_due_sources() -> list[int]:
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Source).where(Source.is_active.is_(True)))
        due_ids = []
        now = datetime.now(timezone.utc)
        for source in result.scalars():
            interval = FREQUENCY_TO_TIMEDELTA.get(source.crawl_frequency, timedelta(weeks=1))
            if source.last_crawled_at is None or (now - source.last_crawled_at) >= interval:
                due_ids.append(source.id)
        return due_ids


@celery_app.task(name="app.tasks.scheduled.crawl_due_sources")
def crawl_due_sources() -> dict:
    """celery-beat entrypoint (hourly, see app/celery_app.py beat_schedule) - re-crawls every
    active Source whose crawl_frequency interval has elapsed since last_crawled_at."""
    due_ids = asyncio.run(_find_due_sources())
    logger.info("due_sources_found", count=len(due_ids))

    for source_id in due_ids:
        recrawl_source.delay(source_id)

    return {"queued": len(due_ids)}


@celery_app.task(name="app.tasks.scheduled.recrawl_source")
def recrawl_source(source_id: int) -> dict:
    return asyncio.run(run_recrawl(source_id))
