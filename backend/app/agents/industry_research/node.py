from app.agents.industry_research.logic import discover_companies
from app.graph.state import DiscoveredCompany, IngestionState


async def industry_research_node(state: IngestionState) -> dict:
    result = await discover_companies(state["seed_query"])

    discovered: list[DiscoveredCompany] = [
        DiscoveredCompany(
            name=c.name,
            website_url=c.website_url,
            snippet=c.snippet,
            source_url=c.source_url,
        )
        for c in result.candidates
    ]
    return {"discovered_companies": discovered}
