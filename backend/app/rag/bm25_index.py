"""In-process BM25 index over Qdrant's text_chunks payloads.

Phase-1 simplification: for millions of documents this should be a proper inverted-index service
(Qdrant's native sparse-vector/BM25 support, OpenSearch, or Elasticsearch) refreshed
incrementally by the Embedding Agent as it writes new chunks - not a full in-memory scroll +
rebuild on every cold start. Documented here rather than hidden, since correctness at seed scale
does not imply correctness at "millions of documents" scale.
"""

from dataclasses import dataclass

from rank_bm25 import BM25Okapi

from app.db.qdrant_client import TEXT_CHUNKS_COLLECTION, get_qdrant_client


@dataclass
class Bm25Corpus:
    tokenized_corpus: list[list[str]]
    payloads: list[dict]
    bm25: BM25Okapi


_cached_corpus: Bm25Corpus | None = None


def _tokenize(text: str) -> list[str]:
    return text.lower().split()


async def build_bm25_corpus(force_refresh: bool = False) -> Bm25Corpus | None:
    global _cached_corpus
    if _cached_corpus is not None and not force_refresh:
        return _cached_corpus

    client = get_qdrant_client()
    payloads: list[dict] = []
    offset = None

    while True:
        points, offset = await client.scroll(
            collection_name=TEXT_CHUNKS_COLLECTION,
            limit=256,
            offset=offset,
            with_payload=True,
            with_vectors=False,
        )
        payloads.extend(point.payload for point in points if point.payload)
        if offset is None:
            break

    if not payloads:
        return None

    tokenized_corpus = [_tokenize(p.get("chunk_text", "")) for p in payloads]
    _cached_corpus = Bm25Corpus(
        tokenized_corpus=tokenized_corpus, payloads=payloads, bm25=BM25Okapi(tokenized_corpus)
    )
    return _cached_corpus
