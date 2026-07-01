"""Hand-picked, freely-crawlable seed sources for Phase 1 (verified live 2026-07-01).

These are real public sites used by scripts/seed_crawl.py to prove the ingestion pipeline
end-to-end. The Industry Research Agent (app/agents/industry_research) discovers further
companies at runtime via web search - this list is only the fixed starting set.
"""
from pydantic import BaseModel


class SeedSource(BaseModel):
    name: str
    base_url: str
    source_type: str
    tos_notes: str = ""


SEED_SOURCES: list[SeedSource] = [
    SeedSource(
        name="Nishijin Textile Industry Association",
        base_url="https://nishijin.or.jp/",
        source_type="association",
        tos_notes="Public industry cooperative site; has an English toggle and a member-weaver directory.",
    ),
    SeedSource(
        name="Hosoo (Nishijin weaving house)",
        base_url="https://www.hosoo.co.jp/en/",
        source_type="website",
        tos_notes="Public company site, English section available.",
    ),
    SeedSource(
        name="JETRO (Japan External Trade Organization)",
        base_url="https://www.jetro.go.jp/en/",
        source_type="gov_site",
        tos_notes="Public government trade-promotion site; survey reports and trade statistics sections.",
    ),
]
