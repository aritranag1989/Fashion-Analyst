from app.agents.trade_intelligence.logic import fetch_and_store_trade_context
from app.agents.trade_intelligence.schemas import TradeContextRequest
from app.db.postgres.base import AsyncSessionLocal
from app.graph.state import IngestionState
from app.logging_conf import get_logger

logger = get_logger(__name__)


async def trade_intelligence_node(state: IngestionState) -> dict:
    """Fetches Japan<->India country-level trade context via UN Comtrade (see logic.py). This is
    background context only - it does not and cannot resolve individual company export/import
    relationships (see docs/data-sources.md for why, and the Phase 2 plan)."""
    errors: list[str] = []
    try:
        async with AsyncSessionLocal() as session:
            await fetch_and_store_trade_context(session, TradeContextRequest())
            await session.commit()
    except Exception as exc:  # noqa: BLE001 - trade context is best-effort, never blocks ingestion
        logger.warning("trade_context_fetch_failed", error=str(exc))
        errors.append(f"trade_context_fetch_failed: {exc}")

    return {"errors": errors}
