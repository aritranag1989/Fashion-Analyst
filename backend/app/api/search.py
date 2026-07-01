from fastapi import APIRouter

from app.graph.query_graph import run_query_graph
from app.schemas.search import SearchRequest, SearchResponse

router = APIRouter(prefix="/search", tags=["search"])


@router.post("", response_model=SearchResponse)
async def search(request: SearchRequest) -> SearchResponse:
    """Natural-language / semantic / faceted / KG search via the full RAG query graph."""
    return await run_query_graph(request)
