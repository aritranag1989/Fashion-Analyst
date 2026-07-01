from qdrant_client.models import FieldCondition, Filter, MatchValue

from app.db.qdrant_client import TEXT_CHUNKS_COLLECTION, get_qdrant_client
from app.graph.state import GraphFact, QueryPlan, RetrievedChunk
from app.kg.neo4j_client import get_neo4j_driver
from app.rag.bm25_index import build_bm25_corpus
from app.rag.embeddings import get_embedding_provider

RRF_K = 60  # standard reciprocal-rank-fusion smoothing constant


async def vector_search(plan: QueryPlan, top_k: int) -> list[RetrievedChunk]:
    provider = get_embedding_provider()
    client = get_qdrant_client()
    vector = await provider.embed_query(plan["semantic_query"])

    query_filter = None
    if plan.get("company_id") is not None:
        query_filter = Filter(
            must=[FieldCondition(key="company_id", match=MatchValue(value=plan["company_id"]))]
        )

    hits = await client.search(
        collection_name=TEXT_CHUNKS_COLLECTION,
        query_vector=vector,
        query_filter=query_filter,
        limit=top_k,
    )

    return [
        RetrievedChunk(
            chunk_text=hit.payload.get("chunk_text", ""),
            source_url=hit.payload.get("source_url", ""),
            source_type=hit.payload.get("source_type", ""),
            company_id=hit.payload.get("company_id"),
            confidence_score=hit.payload.get("confidence_score", 0.0),
            retrieval_method="vector",
            rank_score=hit.score,
        )
        for hit in hits
    ]


async def bm25_search(plan: QueryPlan, top_k: int) -> list[RetrievedChunk]:
    corpus = await build_bm25_corpus()
    if corpus is None:
        return []

    query_tokens = plan["keyword_terms"] or plan["semantic_query"].lower().split()
    scores = corpus.bm25.get_scores(query_tokens)
    ranked = sorted(enumerate(scores), key=lambda pair: pair[1], reverse=True)[:top_k]

    return [
        RetrievedChunk(
            chunk_text=corpus.payloads[i].get("chunk_text", ""),
            source_url=corpus.payloads[i].get("source_url", ""),
            source_type=corpus.payloads[i].get("source_type", ""),
            company_id=corpus.payloads[i].get("company_id"),
            confidence_score=corpus.payloads[i].get("confidence_score", 0.0),
            retrieval_method="bm25",
            rank_score=float(score),
        )
        for i, score in ranked
        if score > 0
    ]


_KG_SEARCH_QUERY = """
MATCH (c:Company)
WHERE toLower(c.name) CONTAINS toLower($term)
OPTIONAL MATCH (c)-[:PRODUCES]->(p:Product)-[:MADE_OF]->(f:Fabric)
OPTIONAL MATCH (c)-[loc:LOCATED_IN]->(city:City)
OPTIONAL MATCH (c)-[exp:EXPORTS_TO]->(country:Country)
RETURN c.company_id AS company_id, c.name AS company_name,
       collect(DISTINCT p.name) AS products, collect(DISTINCT f.name) AS fabrics,
       collect(DISTINCT city.name) AS cities, collect(DISTINCT country.name) AS export_countries,
       loc.source_url AS loc_source, loc.confidence AS loc_confidence
LIMIT 10
"""


async def kg_search(plan: QueryPlan) -> list[GraphFact]:
    if not plan["needs_graph_traversal"]:
        return []

    terms = plan["keyword_terms"] or [plan["semantic_query"]]
    driver = get_neo4j_driver()
    facts: list[GraphFact] = []

    async with driver.session() as session:
        for term in terms[:3]:
            result = await session.run(_KG_SEARCH_QUERY, term=term)
            async for record in result:
                if record["company_name"] is None:
                    continue
                summary_parts = [record["company_name"]]
                if record["products"]:
                    summary_parts.append(f"produces {', '.join(record['products'])}")
                if record["fabrics"]:
                    summary_parts.append(f"using {', '.join(record['fabrics'])}")
                if record["cities"]:
                    summary_parts.append(f"located in {', '.join(record['cities'])}")
                if record["export_countries"]:
                    summary_parts.append(f"exports to {', '.join(record['export_countries'])}")

                facts.append(
                    GraphFact(
                        summary="; ".join(summary_parts),
                        company_id=record["company_id"],
                        confidence=record["loc_confidence"] or 0.5,
                        source_url=record["loc_source"] or "",
                    )
                )

    return facts


def reciprocal_rank_fusion(
    vector_hits: list[RetrievedChunk], bm25_hits: list[RetrievedChunk]
) -> list[RetrievedChunk]:
    """Merges + de-duplicates vector and BM25 results by RRF score, keyed on (source_url, chunk_text)."""
    scores: dict[tuple[str, str], float] = {}
    best_chunk: dict[tuple[str, str], RetrievedChunk] = {}

    for rank_list in (vector_hits, bm25_hits):
        for rank, chunk in enumerate(rank_list):
            key = (chunk["source_url"], chunk["chunk_text"])
            scores[key] = scores.get(key, 0.0) + 1.0 / (RRF_K + rank + 1)
            best_chunk[key] = chunk

    ordered_keys = sorted(scores, key=lambda k: scores[k], reverse=True)
    return [best_chunk[key] for key in ordered_keys]
