from fastapi import APIRouter
from sqlalchemy import select

from app.db.postgres.base import AsyncSessionLocal
from app.db.postgres.models import Source
from app.tasks.ingestion_tasks import run_ingestion_pipeline

router = APIRouter(prefix="/agents", tags=["agents-admin"])

AGENT_NAMES = [
    "industry_research",
    "website_crawling",
    "document_extraction",
    "verification",
    "embedding",
    "knowledge_graph",
    "query_planner",
    "answer_generator",
    "image_understanding",
    "trade_intelligence",
]


@router.get("/status")
async def agents_status() -> dict:
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Source))
        sources = result.scalars().all()

    return {
        "agents": AGENT_NAMES,
        "real_logic": [
            "industry_research",
            "website_crawling",
            "document_extraction",
            "verification",
            "embedding",
            "knowledge_graph",
            "query_planner",
            "answer_generator",
        ],
        "stubbed": ["image_understanding", "trade_intelligence"],
        "tracked_sources": [
            {"id": s.id, "name": s.name, "last_crawled_at": s.last_crawled_at, "is_active": s.is_active}
            for s in sources
        ],
    }


@router.post("/retry/{task_id}")
async def retry_ingestion_task(task_id: str) -> dict:
    result = run_ingestion_pipeline.AsyncResult(task_id)
    if not result.failed():
        return {"retried": False, "reason": "task did not fail"}

    args = result.args or []
    new_task = run_ingestion_pipeline.delay(*args)
    return {"retried": True, "new_task_id": new_task.id}
