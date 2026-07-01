# Data sources

## In scope for Phase 1

Freely-crawlable public sources only:
- Official company/organization websites (discovered via the Industry Research Agent's web
  search, seeded by `backend/app/crawlers/sources/seed_sources.py`).
- JETRO, industry associations (e.g. Nishijin Textile Industry Association), government/industry
  PDF reports, news articles.
- **UN Comtrade** (free public API) for country-level aggregate trade flows by HS code
  (`backend/app/trade/un_comtrade.py`).

## Explicitly out of scope for Phase 1

Panjiva, Volza, ImportYeti, TradeMap, ICEGATE, DGFT, and LinkedIn/Instagram scraping are **not**
implemented. These are either paid/gated (Panjiva, Volza, ImportYeti, TradeMap, licensed ICEGATE
data) or ToS-restricted to scrape at scale (LinkedIn, Instagram).

### Concrete impact on the original research goals

Goals #5-11 from the original spec (finding Japanese exporters to India/Kolkata, Indian importers
of Japanese handwoven fabric, Kolkata companies exporting to Japan, Indo-Japanese textile
collaborations) **cannot be fully answered in Phase 1**. UN Comtrade only provides country-level
aggregates (Japan <-> India totals by HS code) - it has no company-level shipment records and no
city/port granularity, so "Kolkata" specifically is invisible to it.

Any company-to-company trade relationship surfaced by this system in Phase 1 comes only from
crawled text claims (a company's own site saying "we export to India," a news article naming a
deal) - each with its own citation and confidence score, never from a structured trade database.

## Pluggable design for Phase 2

`backend/app/trade/base.py` defines a `TradeDataProvider` interface. UN Comtrade
(`backend/app/trade/un_comtrade.py`) is the only registered implementation
(`backend/app/trade/__init__.py`). Adding Panjiva, Volza, DGFT, or a licensed ICEGATE feed later
means implementing this interface and registering it - no changes needed to the orchestration
graph, API layer, or frontend.

**Recommended Phase 2 priority**: a Panjiva or Volza subscription for company-level shipment
matching, plus a DGFT/ICEGATE data-sharing arrangement or licensed customs-data reseller for the
India side - these two gaps most directly block goals #5-11.
