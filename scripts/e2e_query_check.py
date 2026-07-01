"""Runs one real natural-language query through the full RAG query graph and prints the cited,
confidence-scored answer - proves the anti-hallucination path works both when data exists and
when it doesn't. Run from backend/: `uv run python ../scripts/e2e_query_check.py "<question>"`.
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from app.graph.query_graph import run_query_graph  # noqa: E402
from app.schemas.search import SearchRequest  # noqa: E402


async def main() -> None:
    query = sys.argv[1] if len(sys.argv) > 1 else "What Nishijin textile weavers are in the knowledge base?"
    print(f"Query: {query!r}\n")

    response = await run_query_graph(SearchRequest(query=query))

    print(f"Insufficient data: {response.insufficient_data}")
    print(f"Confidence overall: {response.confidence_overall}")
    print(f"\nAnswer:\n{response.answer}\n")
    print(f"Citations ({len(response.citations)}):")
    for c in response.citations:
        print(f"  - [{c.source_url}] (confidence {c.confidence}): {c.excerpt}")


if __name__ == "__main__":
    asyncio.run(main())
