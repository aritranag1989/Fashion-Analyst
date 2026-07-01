from typing import Annotated, TypedDict

import operator


class DiscoveredCompany(TypedDict):
    name: str
    website_url: str | None
    snippet: str
    source_url: str


class RawPage(TypedDict):
    url: str
    source_id: int
    document_id: int
    document_type: str  # html | pdf
    content_hash: str
    html: str | None
    pdf_bytes: bytes | None
    linked_pdf_urls: list[str]


class CrawledDocument(TypedDict):
    url: str
    source_id: int
    document_id: int
    document_type: str  # html | pdf
    content_hash: str
    text: str
    tables: list[list[list[str | None]]]
    language: str | None


class ExtractedEntity(TypedDict):
    entity_type: str  # company | product | contact | address | association | event
    payload: dict
    document_url: str


class VerificationResult(TypedDict):
    entity_type: str
    payload: dict
    confidence: float
    verification_method: str
    corroborating_source_urls: list[str]
    document_url: str


class IngestionState(TypedDict):
    """Shared state threaded through the ingestion LangGraph
    (industry_research -> website_crawling -> document_extraction -> image_understanding [stub]
    -> verification -> {embedding, knowledge_graph} | flag_for_review -> trade_intelligence [stub]).
    """

    seed_query: str
    discovered_companies: Annotated[list[DiscoveredCompany], operator.add]
    raw_pages: Annotated[list[RawPage], operator.add]
    crawled_documents: Annotated[list[CrawledDocument], operator.add]
    extracted_entities: Annotated[list[ExtractedEntity], operator.add]
    verification_results: Annotated[list[VerificationResult], operator.add]
    flagged_facts: Annotated[list[VerificationResult], operator.add]
    confidence_threshold: float
    errors: Annotated[list[str], operator.add]


class RetrievedChunk(TypedDict):
    chunk_text: str
    source_url: str
    source_type: str
    company_id: int | None
    confidence_score: float
    retrieval_method: str  # vector | bm25
    rank_score: float


class GraphFact(TypedDict):
    summary: str
    company_id: int | None
    confidence: float
    source_url: str


class QueryPlan(TypedDict):
    semantic_query: str
    keyword_terms: list[str]
    company_id: int | None
    fabric_tags: list[str]
    needs_graph_traversal: bool


class QueryState(TypedDict):
    """Shared state threaded through the query LangGraph (query_planner -> parallel
    [vector_search, bm25_search, kg_search] -> fusion -> verification -> answer_generator)."""

    request_query: str
    top_k: int
    request_company_id: int | None
    request_fabric_tags: list[str]
    plan: QueryPlan
    vector_hits: Annotated[list[RetrievedChunk], operator.add]
    bm25_hits: Annotated[list[RetrievedChunk], operator.add]
    graph_facts: Annotated[list[GraphFact], operator.add]
    fused_chunks: list[RetrievedChunk]
    verified_chunks: list[RetrievedChunk]
    confidence_threshold: float
    answer: str
    citations: list[dict]
    confidence_overall: float
    insufficient_data: bool
