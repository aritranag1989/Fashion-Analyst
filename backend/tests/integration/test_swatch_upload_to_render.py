import io

from httpx import ASGITransport, AsyncClient
from PIL import Image
from sqlalchemy import func, select

from app.agents.pattern_designer.schemas import PatternSpecSuggestion, SwatchRoleSuggestion
from app.db.postgres.base import AsyncSessionLocal
from app.db.postgres.models import ConceptShot, PatternMockup, PatternSwatchRole, Swatch
from app.main import app
from app.pattern_rendering.pipeline import clear_all_pattern_data, generate_matrix
from app.pattern_rendering.storage import resolve_path, save_bytes


def _sample_png_bytes(color: tuple[int, int, int]) -> bytes:
    # PNG (lossless) rather than JPEG deliberately: this test's job is the upload -> extraction ->
    # DB row *pipeline*, not re-verifying extraction precision under lossy compression artifacts
    # (a real swatch photo would be a JPEG and could shift a value or two - that's covered, with a
    # controlled input, by test_color_extraction.py's own unit tests instead).
    image = Image.new("RGB", (200, 200), color)
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


async def test_swatch_upload_creates_row_with_extracted_color():
    """Exercises the real POST /swatches/upload route against a real Postgres - proves the
    multipart upload -> color extraction -> DB row chain works end to end."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        files = {"file": ("swatch.png", _sample_png_bytes((26, 43, 60)), "image/png")}
        data = {"label": "Integration test swatch"}
        response = await client.post("/api/v1/swatches/upload", files=files, data=data)

    assert response.status_code == 200
    body = response.json()
    assert body["hex_color"] == "#1a2b3c"
    assert body["label"] == "Integration test swatch"

    async with AsyncSessionLocal() as session:
        swatch = await session.get(Swatch, body["id"])
        assert swatch is not None
        assert swatch.hex_color == "#1a2b3c"

        await session.delete(swatch)
        await session.commit()


async def test_generate_matrix_round_trip(monkeypatch):
    """Bypasses Celery entirely (integration tests shouldn't need a running worker/broker) and
    mocks the PydanticAI designer call (no ANTHROPIC_API_KEY needed) to prove the
    render -> persist -> file-on-disk round trip works against a real Postgres."""
    async with AsyncSessionLocal() as session:
        swatch_a = Swatch(
            label="Ground",
            photo_storage_path="swatch_photos/a.jpg",
            hex_color="#000000",
            rgb_r=0,
            rgb_g=0,
            rgb_b=0,
        )
        swatch_b = Swatch(
            label="Check",
            photo_storage_path="swatch_photos/b.jpg",
            hex_color="#ffffff",
            rgb_r=255,
            rgb_g=255,
            rgb_b=255,
        )
        session.add_all([swatch_a, swatch_b])
        await session.commit()
        await session.refresh(swatch_a)
        await session.refresh(swatch_b)
        swatch_ids = [swatch_a.id, swatch_b.id]

    fake_suggestions = [
        PatternSpecSuggestion(
            pattern_type="pinstripe",
            swatch_roles=[
                SwatchRoleSuggestion(swatch_id=swatch_ids[0], role_index=0),
                SwatchRoleSuggestion(swatch_id=swatch_ids[1], role_index=1),
            ],
            rationale="Test-only suggestion",
        )
    ]

    async def _fake_suggest(available_swatches, num_suggestions=12):
        return fake_suggestions

    # Patch where the name is *used* (pipeline.py's module namespace), not where it's defined.
    monkeypatch.setattr("app.pattern_rendering.pipeline.suggest_pattern_specs", _fake_suggest)

    batch_id = "integration-test-batch"
    mockups = await generate_matrix(
        batch_id=batch_id, swatch_ids=swatch_ids, pattern_types=None, num_llm_suggestions=1
    )

    assert len(mockups) == 1
    mockup = mockups[0]
    assert mockup.pattern_type == "pinstripe"
    assert mockup.batch_id == batch_id
    tile_path = resolve_path(mockup.tile_storage_path)
    assert tile_path.exists()

    async with AsyncSessionLocal() as session:
        roles = (
            (
                await session.execute(
                    select(PatternSwatchRole).where(PatternSwatchRole.mockup_id == mockup.id)
                )
            )
            .scalars()
            .all()
        )
        assert len(roles) == 2

        for role in roles:
            await session.delete(role)
        db_mockup = await session.get(PatternMockup, mockup.id)
        await session.delete(db_mockup)
        for swatch_id in swatch_ids:
            db_swatch = await session.get(Swatch, swatch_id)
            await session.delete(db_swatch)
        await session.commit()

    tile_path.unlink(missing_ok=True)


async def test_clear_all_pattern_data_deletes_everything_and_files(monkeypatch):
    """NOTE: unlike the other tests in this file, clear_all_pattern_data() is a *global* wipe -
    it deletes every Swatch/PatternMockup/PatternSwatchRole/ConceptShot row in the database, not
    just rows this test created. This must stay the LAST test in the file; don't assume tests
    here are safely order-independent once this exists. Its own cleanup *is* the assertion - no
    separate teardown needed since the point is proving zero rows remain."""
    swatch_a = Swatch(
        label="Ground", photo_storage_path="swatch_photos/a.jpg",
        hex_color="#000000", rgb_r=0, rgb_g=0, rgb_b=0,
    )
    swatch_b = Swatch(
        label="Check", photo_storage_path="swatch_photos/b.jpg",
        hex_color="#ffffff", rgb_r=255, rgb_g=255, rgb_b=255,
    )
    async with AsyncSessionLocal() as session:
        session.add_all([swatch_a, swatch_b])
        await session.commit()
        await session.refresh(swatch_a)
        await session.refresh(swatch_b)
        swatch_ids = [swatch_a.id, swatch_b.id]

    fake_suggestions = [
        PatternSpecSuggestion(
            pattern_type="pinstripe",
            swatch_roles=[
                SwatchRoleSuggestion(swatch_id=swatch_ids[0], role_index=0),
                SwatchRoleSuggestion(swatch_id=swatch_ids[1], role_index=1),
            ],
            rationale="Test-only suggestion",
        )
    ]

    async def _fake_suggest(available_swatches, num_suggestions=12):
        return fake_suggestions

    monkeypatch.setattr("app.pattern_rendering.pipeline.suggest_pattern_specs", _fake_suggest)

    mockups = await generate_matrix(
        batch_id="clear-all-test-batch", swatch_ids=swatch_ids, pattern_types=None,
        num_llm_suggestions=1,
    )
    mockup = mockups[0]
    tile_path = resolve_path(mockup.tile_storage_path)
    assert tile_path.exists()

    concept_shot_image_path = save_bytes(b"fake-png-bytes", "concept_shots", "png")
    async with AsyncSessionLocal() as session:
        concept_shot = ConceptShot(
            mockup_id=mockup.id,
            provider_name="openai",
            prompt_used="test prompt",
            image_storage_path=concept_shot_image_path,
            status="completed",
        )
        session.add(concept_shot)
        await session.commit()
    concept_shot_full_path = resolve_path(concept_shot_image_path)
    assert concept_shot_full_path.exists()

    result = await clear_all_pattern_data()

    # >= not == : this is a shared dev Postgres, not an isolated per-test database, so other rows
    # (manual testing via the real frontend, other test runs) may legitimately already be present
    # alongside the ones this test just created. The real contract being proven is "the DB reaches
    # exactly zero afterward" (below), not "exactly what I made was the only thing that existed."
    assert result["swatches_deleted"] >= 2
    assert result["mockups_deleted"] >= 1
    assert result["swatch_roles_deleted"] >= 2
    assert result["concept_shots_deleted"] >= 1

    async with AsyncSessionLocal() as session:
        assert (await session.scalar(select(func.count()).select_from(Swatch))) == 0
        assert (await session.scalar(select(func.count()).select_from(PatternMockup))) == 0
        assert (await session.scalar(select(func.count()).select_from(PatternSwatchRole))) == 0
        assert (await session.scalar(select(func.count()).select_from(ConceptShot))) == 0

    assert not tile_path.exists()
    assert not concept_shot_full_path.exists()
