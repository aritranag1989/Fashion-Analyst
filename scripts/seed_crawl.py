"""Runs the full ingestion pipeline once, directly (no Celery), against a seed query, to prove
the industry_research -> crawling -> extraction -> verification -> embedding -> knowledge_graph
chain works end-to-end. Run from backend/: `uv run python ../scripts/seed_crawl.py`.
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from app.graph.ingestion_graph import run_ingestion  # noqa: E402


async def main() -> None:
    seed_query = sys.argv[1] if len(sys.argv) > 1 else "Nishijin textile weavers in Kyoto"
    print(f"Running ingestion for seed query: {seed_query!r}")

    final_state = await run_ingestion(seed_query)

    print(f"Discovered companies: {len(final_state['discovered_companies'])}")
    print(f"Raw pages crawled: {len(final_state['raw_pages'])}")
    print(f"Documents extracted: {len(final_state['crawled_documents'])}")
    print(f"Verified facts (embedded + graphed): {len(final_state['verification_results'])}")
    for v in final_state["verification_results"]:
        print(f"  - {v['payload'].get('name')} (confidence {v['confidence']})")
    print(f"Flagged for review (below confidence threshold): {len(final_state['flagged_facts'])}")
    for f in final_state["flagged_facts"]:
        print(f"  - {f['payload'].get('name')} (confidence {f['confidence']})")
    if final_state["errors"]:
        print(f"Errors ({len(final_state['errors'])}):")
        for err in final_state["errors"]:
            print(f"  ! {err}")


if __name__ == "__main__":
    asyncio.run(main())
