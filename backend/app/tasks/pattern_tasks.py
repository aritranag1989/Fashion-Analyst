import asyncio

from app.celery_app import celery_app
from app.logging_conf import get_logger
from app.pattern_rendering.pipeline import generate_matrix

logger = get_logger(__name__)


@celery_app.task(name="app.tasks.pattern_tasks.generate_pattern_matrix")
def generate_pattern_matrix(
    batch_id: str,
    swatch_ids: list[int] | None,
    pattern_types: list[str] | None,
    num_llm_suggestions: int = 20,
) -> dict:
    """Celery tasks are sync entrypoints; the pipeline itself is async, so we drive it with
    asyncio.run here (same pattern as tasks/ingestion_tasks.py)."""
    logger.info("pattern_matrix_task_started", batch_id=batch_id)
    mockups = asyncio.run(
        generate_matrix(batch_id, swatch_ids, pattern_types, num_llm_suggestions)
    )
    logger.info("pattern_matrix_task_finished", batch_id=batch_id, rendered_count=len(mockups))
    return {"batch_id": batch_id, "rendered_count": len(mockups)}
