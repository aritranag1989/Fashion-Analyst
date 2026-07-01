from pathlib import Path

from sqlalchemy import select

from app.agents.pattern_designer.logic import suggest_pattern_specs
from app.db.postgres.base import AsyncSessionLocal
from app.db.postgres.models import ConceptShot, PatternMockup, PatternSwatchRole, Swatch
from app.logging_conf import get_logger
from app.pattern_rendering import get_renderer
from app.pattern_rendering.color_extraction import extract_dominant_color
from app.pattern_rendering.schemas import RenderParams, SwatchColor
from app.pattern_rendering.storage import resolve_path, save_bytes, save_image

logger = get_logger(__name__)


async def ingest_swatch(photo_path: str, label: str) -> Swatch:
    """Extracts the dominant color from a swatch photo, stores the photo, and persists a Swatch
    row. Used by both the POST /swatches/upload route and manual scripts."""
    hex_color, r, g, b = extract_dominant_color(photo_path)
    photo_bytes = Path(photo_path).read_bytes()
    extension = Path(photo_path).suffix.lstrip(".").lower() or "jpg"
    storage_path = save_bytes(photo_bytes, "swatch_photos", extension)

    async with AsyncSessionLocal() as session:
        swatch = Swatch(
            label=label,
            photo_storage_path=storage_path,
            hex_color=hex_color,
            rgb_r=r,
            rgb_g=g,
            rgb_b=b,
        )
        session.add(swatch)
        await session.commit()
        await session.refresh(swatch)
        return swatch


async def generate_matrix(
    batch_id: str,
    swatch_ids: list[int] | None,
    pattern_types: list[str] | None,
    num_llm_suggestions: int = 20,
) -> list[PatternMockup]:
    """The core orchestration, called by the Celery task (API-triggered) AND directly by scripts
    (no Celery/FastAPI needed for the batch usage mode): Claude suggests {pattern_type, ordered
    swatches} combinations from the available swatch library, each suggestion is deterministically
    rendered and persisted. The LLM only ever picks combinations - it never touches pixels."""
    async with AsyncSessionLocal() as session:
        query = select(Swatch)
        if swatch_ids:
            query = query.where(Swatch.id.in_(swatch_ids))
        available_swatches = list((await session.execute(query)).scalars().all())

        if not available_swatches:
            logger.warning("generate_matrix_no_swatches", batch_id=batch_id)
            return []

        suggestions = await suggest_pattern_specs(available_swatches, num_llm_suggestions)
        if pattern_types:
            suggestions = [s for s in suggestions if s.pattern_type in pattern_types]

        swatch_by_id = {s.id: s for s in available_swatches}
        mockups: list[PatternMockup] = []

        for spec in suggestions:
            try:
                renderer = get_renderer(spec.pattern_type)
            except KeyError:
                logger.warning("generate_matrix_unknown_pattern_type", pattern_type=spec.pattern_type)
                continue

            ordered_roles = sorted(spec.swatch_roles, key=lambda r: r.role_index)
            if any(r.swatch_id not in swatch_by_id for r in ordered_roles):
                logger.warning("generate_matrix_unknown_swatch_id", batch_id=batch_id)
                continue
            if not (renderer.min_swatches <= len(ordered_roles) <= renderer.max_swatches):
                continue

            params = RenderParams()
            swatch_colors = [
                SwatchColor(
                    swatch_id=role.swatch_id,
                    hex_color=swatch_by_id[role.swatch_id].hex_color,
                    role_index=role.role_index,
                )
                for role in ordered_roles
            ]
            tile = renderer.render_tiled(swatch_colors, params)
            tile_path = save_image(tile, "pattern_tiles")

            mockup = PatternMockup(
                pattern_type=spec.pattern_type,
                render_params=params.model_dump(),
                tile_storage_path=tile_path,
                tile_width_px=tile.width,
                tile_height_px=tile.height,
                design_source="llm_suggested",
                design_rationale=spec.rationale,
                batch_id=batch_id,
            )
            session.add(mockup)
            await session.flush()

            for role in ordered_roles:
                session.add(
                    PatternSwatchRole(mockup_id=mockup.id, swatch_id=role.swatch_id, role_index=role.role_index)
                )

            mockups.append(mockup)

        await session.commit()
        for mockup in mockups:
            await session.refresh(mockup)

        logger.info("generate_matrix_finished", batch_id=batch_id, rendered_count=len(mockups))
        return mockups


async def clear_all_pattern_data() -> dict:
    """Full reset: concept shots, mockups, roles, and swatches alike. Deletes child rows before
    parents in FK-safe order (none of these relationships have cascade configured - see
    delete_swatch in api/swatches.py for the same rationale) and removes each row's backing file
    from disk only after its table's delete has committed - mirroring delete_swatch's
    commit-then-unlink shape rather than one all-or-nothing transaction, so a crash mid-way leaves
    a smaller-but-consistent state instead of an orphaned file or a half-deleted row."""
    async with AsyncSessionLocal() as session:
        concept_shots = list((await session.execute(select(ConceptShot))).scalars().all())
        concept_shot_paths = [
            resolve_path(s.image_storage_path) for s in concept_shots if s.image_storage_path
        ]
        for shot in concept_shots:
            await session.delete(shot)
        await session.commit()
        for path in concept_shot_paths:
            path.unlink(missing_ok=True)

        roles = list((await session.execute(select(PatternSwatchRole))).scalars().all())
        for role in roles:
            await session.delete(role)
        await session.commit()

        mockups = list((await session.execute(select(PatternMockup))).scalars().all())
        mockup_paths = [resolve_path(m.tile_storage_path) for m in mockups]
        for mockup in mockups:
            await session.delete(mockup)
        await session.commit()
        for path in mockup_paths:
            path.unlink(missing_ok=True)

        swatches = list((await session.execute(select(Swatch))).scalars().all())
        swatch_paths = [resolve_path(s.photo_storage_path) for s in swatches]
        for swatch in swatches:
            await session.delete(swatch)
        await session.commit()
        for path in swatch_paths:
            path.unlink(missing_ok=True)

        logger.info(
            "clear_all_pattern_data_finished",
            swatch_count=len(swatches),
            mockup_count=len(mockups),
            role_count=len(roles),
            concept_shot_count=len(concept_shots),
        )
        return {
            "swatches_deleted": len(swatches),
            "mockups_deleted": len(mockups),
            "swatch_roles_deleted": len(roles),
            "concept_shots_deleted": len(concept_shots),
        }
