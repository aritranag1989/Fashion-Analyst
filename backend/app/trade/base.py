from abc import ABC, abstractmethod

from pydantic import BaseModel


class TradeFlowRecord(BaseModel):
    reporter_country: str
    partner_country: str
    hs_code: str
    trade_flow: str  # "import" | "export"
    year: int
    value_usd: float | None = None
    quantity: float | None = None
    source_name: str
    source_url: str


class TradeDataProvider(ABC):
    """Pluggable trade-data source. UN Comtrade (country-level, HS-code aggregate) is the only
    implementation wired in for Phase 1 - see docs/data-sources.md for why Panjiva, Volza,
    ImportYeti, TradeMap, ICEGATE, and DGFT are deferred to Phase 2.

    Adding a company-level provider later (e.g. Panjiva) means implementing this interface and
    registering it in app/trade/__init__.py - no changes to the orchestration graph, API, or
    frontend are required.
    """

    provider_name: str
    granularity: str  # "country" | "company"

    @abstractmethod
    async def get_trade_flows(
        self, reporter_country: str, partner_country: str, hs_code: str | None = None
    ) -> list[TradeFlowRecord]:
        """Fetch trade flow records between two countries, optionally filtered by HS code."""
