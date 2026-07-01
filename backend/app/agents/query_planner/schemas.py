from pydantic import BaseModel, Field


class QueryPlanOutput(BaseModel):
    semantic_query: str = Field(description="Rewritten query optimized for semantic/vector search")
    keyword_terms: list[str] = Field(description="Key nouns/terms for keyword/BM25 search")
    fabric_tags: list[str] = Field(
        default_factory=list, description="Fabric/technique tags mentioned, e.g. kasuri, indigo, silk"
    )
    needs_graph_traversal: bool = Field(
        description="True if the query asks about relationships (supply chains, associations, "
        "trade fairs, exports) that need a knowledge-graph traversal rather than plain text search"
    )
