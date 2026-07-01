from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.postgres.base import get_session
from app.db.postgres.models import TradeData

router = APIRouter(prefix="/trade", tags=["trade"])


@router.get("/comtrade")
async def get_comtrade_flows(
    reporter_country: str,
    partner_country: str,
    hs_code: str | None = None,
    session: AsyncSession = Depends(get_session),
) -> dict:
    """UN Comtrade passthrough - country-level aggregate flows by HS code ONLY. This endpoint
    cannot answer company-level or city-level (e.g. Kolkata-specific) questions - see
    docs/data-sources.md for the Phase 2 plan to add company-level trade providers."""
    query = select(TradeData).where(
        TradeData.reporter_country == reporter_country, TradeData.partner_country == partner_country
    )
    if hs_code:
        query = query.where(TradeData.hs_code == hs_code)

    result = await session.execute(query)
    rows = result.scalars().all()

    return {
        "granularity": "country",
        "caveat": "Country-level aggregate only; no company-level shipment matching in Phase 1.",
        "flows": [
            {
                "reporter_country": r.reporter_country,
                "partner_country": r.partner_country,
                "hs_code": r.hs_code,
                "trade_flow": r.trade_flow,
                "year": r.year,
                "value_usd": r.value_usd,
                "quantity": r.quantity,
            }
            for r in rows
        ],
    }
