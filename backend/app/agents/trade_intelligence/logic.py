"""Trade Intelligence Agent - Phase 1 scope.

Only UN Comtrade (country-level, HS-code aggregate) is wired in - see
backend/app/trade/base.py for the pluggable TradeDataProvider interface and
docs/data-sources.md for the Phase 2 plan to add Panjiva/Volza/DGFT/ICEGATE as
company-level providers without touching this agent's node/graph wiring.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.trade_intelligence.schemas import TradeContextRequest
from app.db.postgres.models import Source, TradeData
from app.logging_conf import get_logger
from app.trade import get_trade_provider

logger = get_logger(__name__)

UN_COMTRADE_SOURCE_NAME = "UN Comtrade"


async def _get_or_create_un_comtrade_source(session: AsyncSession) -> Source:
    result = await session.execute(select(Source).where(Source.name == UN_COMTRADE_SOURCE_NAME))
    source = result.scalar_one_or_none()
    if source is not None:
        return source

    source = Source(
        source_type="trade_api",
        name=UN_COMTRADE_SOURCE_NAME,
        base_url="https://comtradeapi.un.org",
        crawl_frequency="monthly",
        tos_notes="Free public API; country-level aggregate trade flows only.",
    )
    session.add(source)
    await session.flush()
    return source


async def fetch_and_store_trade_context(session: AsyncSession, request: TradeContextRequest) -> int:
    provider = get_trade_provider("un_comtrade")
    records = await provider.get_trade_flows(
        request.reporter_country, request.partner_country, request.hs_code
    )
    if not records:
        return 0

    source = await _get_or_create_un_comtrade_source(session)

    for record in records:
        session.add(
            TradeData(
                reporter_country=record.reporter_country,
                partner_country=record.partner_country,
                hs_code=record.hs_code,
                trade_flow=record.trade_flow,
                year=record.year,
                value_usd=record.value_usd,
                quantity=record.quantity,
                source_id=source.id,
            )
        )

    logger.info("trade_context_stored", records=len(records))
    return len(records)
