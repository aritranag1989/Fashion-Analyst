from langgraph.graph import END, START, StateGraph

from app.agents.document_extraction.node import document_extraction_node
from app.agents.embedding.node import embedding_node
from app.agents.image_understanding.node import image_understanding_node
from app.agents.industry_research.node import industry_research_node
from app.agents.knowledge_graph.node import knowledge_graph_node
from app.agents.trade_intelligence.node import trade_intelligence_node
from app.agents.verification.node import verification_node
from app.agents.website_crawling.node import website_crawling_node
from app.graph.state import IngestionState


def build_ingestion_graph():
    """industry_research -> website_crawling -> document_extraction -> image_understanding [stub]
    -> verification -> {embedding, knowledge_graph} (parallel) -> trade_intelligence [UN Comtrade]
    -> END.

    Below-confidence-threshold facts never reach embedding/knowledge_graph - verification_node
    itself splits verification_results (embedded/graphed) from flagged_facts (review queue only).
    """
    graph = StateGraph(IngestionState)

    graph.add_node("industry_research", industry_research_node)
    graph.add_node("website_crawling", website_crawling_node)
    graph.add_node("document_extraction", document_extraction_node)
    graph.add_node("image_understanding", image_understanding_node)
    graph.add_node("verification", verification_node)
    graph.add_node("embedding", embedding_node)
    graph.add_node("knowledge_graph", knowledge_graph_node)
    graph.add_node("trade_intelligence", trade_intelligence_node)

    graph.add_edge(START, "industry_research")
    graph.add_edge("industry_research", "website_crawling")
    graph.add_edge("website_crawling", "document_extraction")
    graph.add_edge("document_extraction", "image_understanding")
    graph.add_edge("image_understanding", "verification")
    graph.add_edge("verification", "embedding")
    graph.add_edge("verification", "knowledge_graph")
    graph.add_edge("embedding", "trade_intelligence")
    graph.add_edge("knowledge_graph", "trade_intelligence")
    graph.add_edge("trade_intelligence", END)

    return graph.compile()


ingestion_graph = build_ingestion_graph()


async def run_ingestion(seed_query: str, confidence_threshold: float = 0.6) -> IngestionState:
    initial_state: IngestionState = {
        "seed_query": seed_query,
        "discovered_companies": [],
        "raw_pages": [],
        "crawled_documents": [],
        "extracted_entities": [],
        "verification_results": [],
        "flagged_facts": [],
        "confidence_threshold": confidence_threshold,
        "errors": [],
    }
    return await ingestion_graph.ainvoke(initial_state)
