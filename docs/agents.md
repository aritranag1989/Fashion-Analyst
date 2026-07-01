# Agents

Each agent lives at `backend/app/agents/<name>/` with the same shape: `schemas.py` (Pydantic I/O
models), `prompts.py`, `logic.py` (the actual work), `node.py` (the LangGraph node wrapper). This
uniform shape means upgrading a stub to real logic later is a drop-in replacement.

| Agent | Status | What it does |
|---|---|---|
| Industry Research | Real | Claude + server-side web search discovers real Japanese textile companies (`logic.py` uses the raw Anthropic SDK directly - see the ADR on why it bypasses PydanticAI for this one agent). |
| Website Crawling | Real | Playwright-based crawling with robots.txt + rate-limit enforcement (`app/crawlers/robots.py`), records `Source`/`Document` rows. |
| Document Extraction | Real | Parses crawled HTML (`app/extraction/html_parser.py`) and linked PDFs (`app/extraction/pdf_parser.py`), including table extraction for catalogs. |
| Verification | Real | Extracts structured company facts via a PydanticAI/Claude agent, cross-corroborates across sources with fuzzy name matching, scores confidence, and persists only above-threshold facts. |
| Embedding | Real | Chunks verified document text (LlamaIndex splitter) and catalog tables, embeds via the swappable `EmbeddingProvider` (Voyage default), upserts into Qdrant with full provenance payload. |
| Knowledge Graph | Real | Writes verified companies/products/fabrics/certifications/locations into Neo4j with `source_url`/`confidence`/`extracted_at` on every relationship. |
| Query Planner | Real | Decomposes a natural-language question into a semantic query, keyword terms, fabric tags, and whether graph traversal is needed. |
| Answer Generator | Real | Generates a citation-only answer from verified context; returns `insufficient_data=true` rather than guessing when nothing clears the confidence threshold. |
| Image Understanding | Stub | Inert but real-shaped module (see `logic.py` docstring for the Phase 2 activation plan: OCR, populate the `images` Qdrant collection). |
| Trade Intelligence | Stub-but-pluggable | Wired to UN Comtrade (real country-level data) via the `TradeDataProvider` interface; company-level providers are a Phase 2 addition (see `docs/data-sources.md`). |
