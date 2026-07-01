import tempfile
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.postgres.base import get_session
from app.db.postgres.models import PatternSwatchRole, Swatch
from app.pattern_rendering.pipeline import ingest_swatch
from app.pattern_rendering.storage import resolve_path

router = APIRouter(prefix="/swatches", tags=["swatches"])


class SwatchUpdateRequest(BaseModel):
    label: str | None = None
    notes: str | None = None


def _swatch_to_dict(swatch: Swatch) -> dict:
    return {
        "id": swatch.id,
        "label": swatch.label,
        "hex_color": swatch.hex_color,
        "rgb_r": swatch.rgb_r,
        "rgb_g": swatch.rgb_g,
        "rgb_b": swatch.rgb_b,
        "photo_storage_path": swatch.photo_storage_path,
        "notes": swatch.notes,
        "created_at": swatch.created_at,
    }


@router.post("/upload")
async def upload_swatch(file: UploadFile = File(...), label: str = Form(...)) -> dict:
    """Extracts the dominant color synchronously - a single swatch photo is sub-second, no Celery
    needed for this (this is a few-dozen-swatch one-time batch, not a high-volume pipeline)."""
    suffix = Path(file.filename or "swatch.jpg").suffix or ".jpg"
    contents = await file.read()
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(contents)
        tmp_path = tmp.name
    try:
        swatch = await ingest_swatch(tmp_path, label)
    finally:
        Path(tmp_path).unlink(missing_ok=True)
    return _swatch_to_dict(swatch)


@router.get("")
async def list_swatches(
    limit: int = 100, offset: int = 0, session: AsyncSession = Depends(get_session)
) -> list[dict]:
    result = await session.execute(select(Swatch).order_by(Swatch.id).limit(limit).offset(offset))
    return [_swatch_to_dict(s) for s in result.scalars()]


@router.get("/{swatch_id}")
async def get_swatch(swatch_id: int, session: AsyncSession = Depends(get_session)) -> dict:
    swatch = await session.get(Swatch, swatch_id)
    if swatch is None:
        raise HTTPException(status_code=404, detail="Swatch not found")
    return _swatch_to_dict(swatch)


@router.patch("/{swatch_id}")
async def update_swatch(
    swatch_id: int, request: SwatchUpdateRequest, session: AsyncSession = Depends(get_session)
) -> dict:
    swatch = await session.get(Swatch, swatch_id)
    if swatch is None:
        raise HTTPException(status_code=404, detail="Swatch not found")
    if request.label is not None:
        swatch.label = request.label
    if request.notes is not None:
        swatch.notes = request.notes
    await session.commit()
    await session.refresh(swatch)
    return _swatch_to_dict(swatch)


@router.get("/{swatch_id}/photo")
async def get_swatch_photo(
    swatch_id: int, session: AsyncSession = Depends(get_session)
) -> FileResponse:
    swatch = await session.get(Swatch, swatch_id)
    if swatch is None:
        raise HTTPException(status_code=404, detail="Swatch not found")
    return FileResponse(resolve_path(swatch.photo_storage_path))


@router.delete("/{swatch_id}")
async def delete_swatch(swatch_id: int, session: AsyncSession = Depends(get_session)) -> dict:
    swatch = await session.get(Swatch, swatch_id)
    if swatch is None:
        raise HTTPException(status_code=404, detail="Swatch not found")

    # pattern_swatch_roles.swatch_id is NOT NULL, so deleting a swatch that's already used in a
    # rendered mockup would otherwise crash with an IntegrityError (SQLAlchemy's default
    # relationship behavior tries to null out the FK, not cascade or block). Block it explicitly
    # instead, with a clear message, so existing mockups/concept shots are never silently lost.
    usage_count = await session.scalar(
        select(func.count()).select_from(PatternSwatchRole).where(PatternSwatchRole.swatch_id == swatch_id)
    )
    if usage_count:
        raise HTTPException(
            status_code=409,
            detail=f"Cannot delete '{swatch.label}': it's used in {usage_count} existing pattern "
            "mockup(s). Delete those mockups first if you really want to remove this swatch.",
        )

    photo_path = resolve_path(swatch.photo_storage_path)
    await session.delete(swatch)
    await session.commit()
    photo_path.unlink(missing_ok=True)
    return {"deleted": True}
