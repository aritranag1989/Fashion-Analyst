from langgraph.graph import END, START, StateGraph

from app.agents.answer_generator.node import answer_generator_node
from app.agents.query_planner.node import query_planner_node
from app.config import get_settings
from app.graph.state import QueryState
from app.rag.hybrid_search import bm25_search, kg_search, reciprocal_rank_fusion, vector_search
from app.schemas.search import Citation, CompanyResult, SearchRequest, SearchResponse


async def vector_search_node(state: QueryState) -> dict:
    hits = await vector_search(state["plan"], state["top_k"])
    return {"vector_hits": hits}


async def bm25_search_node(state: QueryState) -> dict:
    hits = await bm25_search(state["plan"], state["top_k"])
    return {"bm25_hits": hits}


async def kg_search_node(state: QueryState) -> dict:
    facts = await kg_search(state["plan"])
    return {"graph_facts": facts}


async def fusion_node(state: QueryState) -> dict:
    fused = reciprocal_rank_fusion(state["vector_hits"], state["bm25_hits"])
    return {"fused_chunks": fused[: state["top_k"]]}


async def verification_node(state: QueryState) -> dict:
    """Query-time defense in depth: re-checks the confidence score already attached at ingestion
    time (see app.agents.verification) and drops anything below threshold, even though embedding
    only ever wrote above-threshold chunks - protects against a threshold lowered after ingestion."""
    threshold = state["confidence_threshold"]
    verified = [c for c in state["fused_chunks"] if c["confidence_score"] >= threshold]
    return {"verified_chunks": verified}


def build_query_graph():
    graph = StateGraph(QueryState)

    graph.add_node("query_planner", query_planner_node)
    graph.add_node("vector_search", vector_search_node)
    graph.add_node("bm25_search", bm25_search_node)
    graph.add_node("kg_search", kg_search_node)
    graph.add_node("fusion", fusion_node)
    graph.add_node("verification", verification_node)
    graph.add_node("answer_generator", answer_generator_node)

    graph.add_edge(START, "query_planner")
    graph.add_edge("query_planner", "vector_search")
    graph.add_edge("query_planner", "bm25_search")
    graph.add_edge("query_planner", "kg_search")
    graph.add_edge("vector_search", "fusion")
    graph.add_edge("bm25_search", "fusion")
    graph.add_edge("kg_search", "verification")
    graph.add_edge("fusion", "verification")
    graph.add_edge("verification", "answer_generator")
    graph.add_edge("answer_generator", END)

    return graph.compile()


query_graph = build_query_graph()


async def run_query_graph(request: SearchRequest) -> SearchResponse:
    settings = get_settings()

    initial_state: QueryState = {
        "request_query": request.query,
        "top_k": request.top_k,
        "request_company_id": request.company_id,
        "request_fabric_tags": request.fabric_tags,
        "plan": {
            "semantic_query": request.query,
            "keyword_terms": [],
            "company_id": request.company_id,
            "fabric_tags": request.fabric_tags,
            "needs_graph_traversal": False,
        },
        "vector_hits": [],
        "bm25_hits": [],
        "graph_facts": [],
        "fused_chunks": [],
        "verified_chunks": [],
        "confidence_threshold": settings.confidence_threshold,
        "answer": "",
        "citations": [],
        "confidence_overall": 0.0,
        "insufficient_data": False,
    }

    final_state = await query_graph.ainvoke(initial_state)

    citations = [
        Citation(
            source_url=c["source_url"],
            source_type="verified_chunk",
            excerpt=c["excerpt"],
            confidence=final_state["confidence_overall"],
        )
        for c in final_state["citations"]
    ]

    companies = [
        CompanyResult(company_id=chunk["company_id"])
        for chunk in final_state["verified_chunks"]
        if chunk["company_id"] is not None
    ]
    seen_ids = set()
    deduped_companies = []
    for company in companies:
        if company.company_id not in seen_ids:
            seen_ids.add(company.company_id)
            deduped_companies.append(company)

    return SearchResponse(
        answer=final_state["answer"],
        citations=citations,
        companies=deduped_companies,
        confidence_overall=final_state["confidence_overall"],
        insufficient_data=final_state["insufficient_data"],
    )
