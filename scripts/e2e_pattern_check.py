"""Runs the swatch-upload -> color-extraction -> LLM-suggestion -> deterministic-render pipeline
once, directly (no Celery, no FastAPI server), against a couple of sample swatch photos, to prove
the full chain works end-to-end. Requires a live ANTHROPIC_API_KEY for the pattern_designer step
and a reachable Postgres (docker-compose data services). Requesting the one concept shot at the
end additionally requires a live OPENAI_API_KEY. Run from backend/:
`uv run python ../scripts/e2e_pattern_check.py [<path_to_swatch_photo> ...]`
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from app.pattern_rendering.pipeline import generate_matrix, ingest_swatch  # noqa: E402


async def main() -> None:
    photo_paths = sys.argv[1:] or [
        str(Path(__file__).resolve().parent / "fixtures" / "sample_swatch_1.jpg"),
        str(Path(__file__).resolve().parent / "fixtures" / "sample_swatch_2.jpg"),
    ]
    print(f"Ingesting {len(photo_paths)} swatch photo(s)...")
    swatch_ids = []
    for path in photo_paths:
        swatch = await ingest_swatch(path, label=Path(path).stem)
        print(f"  - swatch {swatch.id}: {swatch.label} -> {swatch.hex_color}")
        swatch_ids.append(swatch.id)

    print("\nGenerating pattern matrix (LLM-suggested combinations, deterministic render)...")
    mockups = await generate_matrix(
        batch_id="manual-e2e-check", swatch_ids=swatch_ids, pattern_types=None, num_llm_suggestions=6
    )
    print(f"Rendered {len(mockups)} mockups:")
    for mockup in mockups:
        print(f"  - [{mockup.pattern_type}] {mockup.design_rationale or '(manual)'} -> {mockup.tile_storage_path}")

    if not mockups:
        return

    # Exactly one concept shot, not looped over every mockup - this mirrors the feature's own
    # cost-control design (the paid AI step is always a deliberate, one-at-a-time action).
    print(f"\nRequesting one AI concept shot for mockup {mockups[0].id} (costs real money)...")
    from app.imagegen import get_imagegen_provider
    from app.pattern_rendering.storage import resolve_path, save_bytes

    provider = get_imagegen_provider()
    tile_path = resolve_path(mockups[0].tile_storage_path)
    result = await provider.generate_concept_shot(str(tile_path), mockups[0].pattern_type)
    saved_path = save_bytes(result.image_bytes, "concept_shots", "png")
    print(f"  - saved concept shot to {saved_path} (provider={result.provider_name})")


if __name__ == "__main__":
    asyncio.run(main())
