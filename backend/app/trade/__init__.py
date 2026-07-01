from functools import lru_cache

from app.trade.base import TradeDataProvider
from app.trade.un_comtrade import UNComtradeProvider

# Phase 2: register additional providers here (Panjiva, Volza, DGFT, ICEGATE) once access is
# secured - see docs/data-sources.md.
_PROVIDERS: dict[str, type[TradeDataProvider]] = {
    "un_comtrade": UNComtradeProvider,
}


@lru_cache
def get_trade_provider(name: str = "un_comtrade") -> TradeDataProvider:
    return _PROVIDERS[name]()
