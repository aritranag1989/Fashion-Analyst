from fastapi import APIRouter
from pydantic import BaseModel

from app.tasks.ingestion_tasks import run_ingestion_pipeline

router = APIRouter(prefix="/ingestion", tags=["ingestion"])


class IngestionTriggerRequest(BaseModel):
    seed_query: str
    confidence_threshold: float = 0.6


class IngestionTriggerResponse(BaseModel):
    task_id: str


@router.post("/trigger", response_model=IngestionTriggerResponse)
async def trigger_ingestion(request: IngestionTriggerRequest) -> IngestionTriggerResponse:
    task = run_ingestion_pipeline.delay(request.seed_query, request.confidence_threshold)
    return IngestionTriggerResponse(task_id=task.id)


@router.get("/status/{task_id}")
async def ingestion_status(task_id: str) -> dict:
    result = run_ingestion_pipeline.AsyncResult(task_id)
    return {"task_id": task_id, "status": result.status, "result": result.result if result.ready() else None}
