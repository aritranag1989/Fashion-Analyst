import asyncio

from app.celery_app import celery_app
from app.graph.ingestion_graph import run_ingestion
from app.logging_conf import get_logger

logger = get_logger(__name__)


@celery_app.task(name="app.tasks.ingestion_tasks.run_ingestion_pipeline")
def run_ingestion_pipeline(seed_query: str, confidence_threshold: float = 0.6) -> dict:
    """Runs the full LangGraph ingestion graph for one seed query. Celery tasks are sync
    entrypoints; the graph itself is async, so we drive it with asyncio.run here."""
    logger.info("ingestion_task_started", seed_query=seed_query)
    final_state = asyncio.run(run_ingestion(seed_query, confidence_threshold))
    logger.info(
        "ingestion_task_finished",
        seed_query=seed_query,
        verified=len(final_state["verification_results"]),
        flagged=len(final_state["flagged_facts"]),
        errors=len(final_state["errors"]),
    )
    return {
        "verified_count": len(final_state["verification_results"]),
        "flagged_count": len(final_state["flagged_facts"]),
        "errors": final_state["errors"],
    }
