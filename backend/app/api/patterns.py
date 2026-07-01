import uuid

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.postgres.base import get_session
from app.db.postgres.models import ConceptShot, PatternMockup, PatternSwatchRole, Swatch
from app.imagegen import get_imagegen_provider
from app.logging_conf import get_logger
from app.pattern_rendering.pipeline import clear_all_pattern_data
from app.pattern_rendering.storage import resolve_path, save_bytes
from app.tasks.pattern_tasks import generate_pattern_matrix

router = APIRouter(prefix="/patterns", tags=["patterns"])
logger = get_logger(__name__)


class PatternMatrixRequest(BaseModel):
    swatch_ids: list[int] | None = None
    pattern_types: list[str] | None = None
    num_llm_suggestions: int = Field(default=20, ge=1, le=50)


class PatternMatrixTriggerResponse(BaseModel):
    task_id: str
    batch_id: str


class ConceptShotRequest(BaseModel):
    garment_type: str | None = None


def _concept_shot_to_dict(shot: ConceptShot) -> dict:
    return {
        "id": shot.id,
        "mockup_id": shot.mockup_id,
        "provider_name": shot.provider_name,
        "garment_type": shot.garment_type,
        "status": shot.status,
        "error_message": shot.error_message,
        "created_at": shot.created_at,
    }


async def _mockup_to_dict(mockup: PatternMockup, session: AsyncSession) -> dict:
    roles_result = await session.execute(
        select(PatternSwatchRole, Swatch)
        .join(Swatch, PatternSwatchRole.swatch_id == Swatch.id)
        .where(PatternSwatchRole.mockup_id == mockup.id)
        .order_by(PatternSwatchRole.role_index)
    )
    swatch_roles = [
        {
            "swatch_id": swatch.id,
            "role_index": role.role_index,
            "hex_color": swatch.hex_color,
            "label": swatch.label,
        }
        for role, swatch in roles_result.all()
    ]
    return {
        "id": mockup.id,
        "pattern_type": mockup.pattern_type,
        "render_params": mockup.render_params,
        "design_source": mockup.design_source,
        "design_rationale": mockup.design_rationale,
        "batch_id": mockup.batch_id,
        "created_at": mockup.created_at,
        "swatch_roles": swatch_roles,
    }


@router.delete("/clear-all")
async def clear_all_pattern_data_route(
    confirm: bool = False, session: AsyncSession = Depends(get_session)
) -> dict:
    """Full reset of the swatch/pattern-mockup library. Concept shots cost real money
    (gpt-image-1), so if any exist and confirm wasn't passed, block with a 409 naming exact
    counts rather than silently deleting them - same shape as delete_swatch's usage-count check."""
    swatch_count = await session.scalar(select(func.count()).select_from(Swatch))
    mockup_count = await session.scalar(select(func.count()).select_from(PatternMockup))
    concept_shot_count = await session.scalar(select(func.count()).select_from(ConceptShot))

    if concept_shot_count and not confirm:
        raise HTTPException(
            status_code=409,
            detail=f"This will permanently delete {swatch_count} swatch(es), {mockup_count} "
            f"pattern mockup(s), and {concept_shot_count} AI concept shot(s) (paid image-gen "
            "calls, not recoverable). Call again with confirm=true to proceed.",
        )

    return await clear_all_pattern_data()


@router.post("/generate", response_model=PatternMatrixTriggerResponse)
async def generate_matrix_route(request: PatternMatrixRequest) -> PatternMatrixTriggerResponse:
    batch_id = uuid.uuid4().hex
    task = generate_pattern_matrix.delay(
        batch_id, request.swatch_ids, request.pattern_types, request.num_llm_suggestions
    )
    return PatternMatrixTriggerResponse(task_id=task.id, batch_id=batch_id)


@router.get("/status/{task_id}")
async def generation_status(task_id: str) -> dict:
    result = generate_pattern_matrix.AsyncResult(task_id)
    return {
        "task_id": task_id,
        "status": result.status,
        "result": result.result if result.ready() else None,
    }


@router.get("/mockups")
async def list_mockups(
    batch_id: str | None = None,
    pattern_type: str | None = None,
    limit: int = 100,
    offset: int = 0,
    session: AsyncSession = Depends(get_session),
) -> list[dict]:
    query = select(PatternMockup)
    if batch_id:
        query = query.where(PatternMockup.batch_id == batch_id)
    if pattern_type:
        query = query.where(PatternMockup.pattern_type == pattern_type)
    query = query.order_by(PatternMockup.id).limit(limit).offset(offset)

    result = await session.execute(query)
    mockups = result.scalars().all()
    return [await _mockup_to_dict(m, session) for m in mockups]


@router.get("/mockups/{mockup_id}")
async def get_mockup(mockup_id: int, session: AsyncSession = Depends(get_session)) -> dict:
    mockup = await session.get(PatternMockup, mockup_id)
    if mockup is None:
        raise HTTPException(status_code=404, detail="Mockup not found")
    return await _mockup_to_dict(mockup, session)


@router.get("/mockups/{mockup_id}/tile")
async def get_mockup_tile(
    mockup_id: int, session: AsyncSession = Depends(get_session)
) -> FileResponse:
    mockup = await session.get(PatternMockup, mockup_id)
    if mockup is None:
        raise HTTPException(status_code=404, detail="Mockup not found")
    return FileResponse(resolve_path(mockup.tile_storage_path))


@router.post("/mockups/{mockup_id}/concept-shot")
async def request_concept_shot(
    mockup_id: int, request: ConceptShotRequest, session: AsyncSession = Depends(get_session)
) -> dict:
    """Synchronous by design: a deliberate, one-at-a-time, costed action (unlike the free/instant
    matrix of deterministic renders), so a single blocking request with a frontend spinner is
    preferable to adding a second polling loop for a single item."""
    mockup = await session.get(PatternMockup, mockup_id)
    if mockup is None:
        raise HTTPException(status_code=404, detail="Mockup not found")

    provider = get_imagegen_provider()
    tile_path = resolve_path(mockup.tile_storage_path)

    try:
        result = await provider.generate_concept_shot(
            str(tile_path), mockup.pattern_type, request.garment_type
        )
        image_path = save_bytes(result.image_bytes, "concept_shots", "png")
        concept_shot = ConceptShot(
            mockup_id=mockup.id,
            provider_name=result.provider_name,
            prompt_used=result.prompt_used,
            garment_type=request.garment_type,
            image_storage_path=image_path,
            status="completed",
        )
    except Exception as exc:  # noqa: BLE001 - report status, don't crash the endpoint
        logger.warning("concept_shot_failed", mockup_id=mockup_id, error=str(exc))
        concept_shot = ConceptShot(
            mockup_id=mockup.id,
            provider_name=provider.provider_name,
            garment_type=request.garment_type,
            status="failed",
            error_message=str(exc),
        )

    session.add(concept_shot)
    await session.commit()
    await session.refresh(concept_shot)
    return _concept_shot_to_dict(concept_shot)


@router.get("/mockups/{mockup_id}/concept-shots")
async def list_concept_shots(
    mockup_id: int, session: AsyncSession = Depends(get_session)
) -> list[dict]:
    result = await session.execute(
        select(ConceptShot).where(ConceptShot.mockup_id == mockup_id).order_by(ConceptShot.id)
    )
    return [_concept_shot_to_dict(s) for s in result.scalars()]


@router.get("/concept-shots/{shot_id}/image")
async def get_concept_shot_image(
    shot_id: int, session: AsyncSession = Depends(get_session)
) -> FileResponse:
    shot = await session.get(ConceptShot, shot_id)
    if shot is None or not shot.image_storage_path:
        raise HTTPException(status_code=404, detail="Concept shot image not found")
    return FileResponse(resolve_path(shot.image_storage_path))
