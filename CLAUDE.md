# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Japan Fashion & Handloom Intelligence Platform ("Fashion Analyst") — a multi-agent RAG research
platform (not a chatbot) that builds a searchable, cited, confidence-scored knowledge base of the
Japanese handloom/handwoven textile industry from public sources. Full design docs live in `docs/`:

- `docs/architecture.md` — data stores, the two LangGraph pipelines, the anti-hallucination mechanism
- `docs/agents.md` — per-agent status (real vs. stub) and responsibilities
- `docs/data-sources.md` — what's in/out of scope for Phase 1, and why
- `docs/adr/0001-orchestration-framework.md` — why LangGraph over CrewAI, and where PydanticAI/LlamaIndex fit

Read those for rationale — this file states rules and conventions, not the reasoning behind them.

## Commands

All backend commands must run with **`backend/` as the working directory** — `app/config.py` loads
`../infra/env/.env` as a path relative to the process's cwd, not to `config.py`'s location, so
running from the repo root silently fails to load real secrets and falls back to in-code defaults.

### Backend setup / run
```
uv sync                                  # installs deps; dev group (pytest/ruff/mypy) included by default
uv run alembic upgrade head              # apply Postgres migrations
uv run uvicorn app.main:app --reload     # dev server on :8000
uv run celery -A app.celery_app worker --loglevel=INFO -Q crawl,celery
uv run celery -A app.celery_app beat --loglevel=INFO
```

### Data services
```
docker compose -f docker/docker-compose.yml up -d postgres neo4j qdrant redis
```
The same compose file also defines `backend`/`worker`/`beat`/`frontend` containers for a full
containerized run.

### Lint / typecheck / test (backend)
```
uv run ruff check .
uv run mypy app
uv run pytest                                              # asyncio_mode=auto, no @pytest.mark.asyncio needed
uv run pytest tests/unit/test_some_module.py::test_name    # single test
```

### Frontend (run from `frontend/`)
```
npm run dev / build / start / lint
```

### Manual end-to-end checks
No automated test covers the graphs yet (see Test expectations). These scripts are the real
end-to-end proof and require live `ANTHROPIC_API_KEY` / `VOYAGE_API_KEY`. Run from `backend/`:
```
uv run python ../scripts/seed_crawl.py "<seed query>"        # runs the ingestion graph once, no Celery
uv run python ../scripts/e2e_query_check.py "<question>"     # runs the query graph, prints cited answer
```

## Architecture rules

- **LangGraph is the only orchestrator.** Two `StateGraph`s exist: `backend/app/graph/ingestion_graph.py`
  and `backend/app/graph/query_graph.py`, with shared `TypedDict` states in `backend/app/graph/state.py`.
  ADR 0001 deliberately rejected CrewAI and rejected running multiple orchestration frameworks in
  parallel — don't reintroduce either.
- **PydanticAI only wraps single Claude calls inside LangGraph nodes**, via the `make_structured_agent()`
  factory in `backend/app/agents/base.py`. It is not a competing orchestrator.
  - One deliberate exception: `backend/app/agents/industry_research/logic.py` calls the raw `anthropic`
    SDK directly because it needs Claude's server-side `web_search_20250305` tool, which PydanticAI
    doesn't expose. Don't generalize this exception to other agents.
- **LlamaIndex is only a chunking utility** (`backend/app/rag/chunking.py`), not used for its own
  agent/workflow abstractions.
- **Every agent has the same 4-file shape** at `backend/app/agents/<name>/`: `schemas.py` (Pydantic
  I/O models), `prompts.py`, `logic.py` (the real, framework-agnostic work), `node.py` (thin LangGraph
  wrapper, function named `<name>_node`). When upgrading a stub (Image Understanding, or a
  company-level Trade Intelligence provider) to real logic, keep this shape so it's a drop-in swap.
- **Anti-hallucination is structural, not a prompt instruction.** Every extracted fact traces to a
  `source_id`; a `ConfidenceScore` is computed from cross-source corroboration
  (`backend/app/agents/verification/logic.py`); anything below `settings.confidence_threshold` is
  written only to the `flagged_facts` review queue and never reaches Qdrant/Neo4j. The query graph
  re-checks confidence again at query time (`verification_node` in `query_graph.py`) as defense in
  depth — don't remove that second check just because ingestion already filtered. Answer generation
  must return `insufficient_data=true` without calling Claude when no verified context clears the
  bar — don't collapse that early-return path.
- **Swappable-provider pattern**: embeddings (`backend/app/rag/embeddings/`) and trade data
  (`backend/app/trade/`) both follow the same shape — an ABC in `base.py`, concrete implementations
  as siblings, and a `get_*()`/registration function in `__init__.py` that picks the implementation
  from settings. Follow this shape for any new pluggable backend instead of branching inline on a
  provider string.
- **Provenance columns are mandatory on new tables**: anything holding crawled/extracted data needs
  a `source_id` FK to `sources`, and a `confidence_score_id` FK if the value is a scored fact rather
  than raw metadata.
- Celery currently runs the *entire* ingestion pipeline as one task per seed query
  (`backend/app/celery_app.py`), with LangGraph doing the fine-grained chaining inside that one task.
  The queue names already reserve a future per-stage split — read the rationale comment in
  `celery_app.py` before splitting tasks per stage/queue.
- **Known gap**: `ensure_collections()` (`backend/app/db/qdrant_collections.py`) and `apply_schema()`
  (`backend/app/kg/schema.py`) create the Qdrant collections/payload indexes and Neo4j
  constraints/indexes respectively, but neither is currently invoked from `app/main.py` startup or
  anywhere else in the codebase. Call them explicitly against a fresh environment before relying on
  those collections/constraints existing.
- `infra/k8s/` is an explicitly unvalidated placeholder (see its README) — Phase 1 runs on
  `docker/docker-compose.yml` only. Don't treat the k8s manifests as a working deployment target.

## Repo map

```
backend/app/
  agents/<name>/         schemas.py, prompts.py, logic.py, node.py per agent (docs/agents.md has status)
  graph/                 ingestion_graph.py, query_graph.py, state.py (shared TypedDict states)
  api/                   FastAPI routers: health, search, companies, trade, agents_admin, ingestion
  db/postgres/            SQLAlchemy models + async session/engine (system of record + provenance)
  kg/                     Neo4j driver + schema.py (constraints/indexes, example Cypher patterns)
  rag/                    hybrid_search.py, bm25_index.py, chunking.py, embeddings/ (provider ABC)
  trade/                  TradeDataProvider ABC + un_comtrade.py implementation
  crawlers/               Playwright crawling, robots.py, scrapy_project/, sources/ (seed list)
  extraction/             html_parser.py, pdf_parser.py, catalog_parser.py
  tasks/                  Celery tasks: ingestion_tasks.py, scheduled.py
  config.py, celery_app.py, main.py, logging_conf.py
backend/tests/{unit,integration}/   currently empty — see Test expectations
backend/alembic/versions/           0001_initial_schema.py is the only migration so far
scripts/                 seed_crawl.py, e2e_query_check.py — manual e2e runners, not pytest-wrapped
frontend/src/
  app/                   Next.js App Router pages: /, search, companies, companies/[id],
                         companies/compare, graph, map, timeline, trade, admin
  components/             e.g. components/search/SearchExperience.tsx
  lib/                     api-client.ts (fetch wrapper), types.ts (wire-format interfaces)
docker/                  docker-compose.yml + Dockerfile.backend / .worker / .frontend
infra/env/               .env / .env.example (real .env is gitignored — never commit real keys)
infra/k8s/               placeholder manifests, not validated (see Architecture rules)
docs/                    architecture.md, agents.md, data-sources.md, adr/
```

## Naming conventions

- **Python**: `snake_case` for functions/variables/modules; `PascalCase` for Pydantic models and
  SQLAlchemy models; `UPPER_SNAKE_CASE` for module-level constants (`FUZZY_MATCH_THRESHOLD`,
  `MAX_TEXT_CHARS_FOR_EXTRACTION`). Module-level singletons meant to be private are prefixed with
  `_` (`_extraction_agent`, `_EGO_NETWORK_QUERY`).
- LangGraph node functions are always named `<agent_name>_node` and live in that agent's `node.py`;
  graph state `TypedDict`s live centrally in `graph/state.py`, not scattered per agent.
- FastAPI routers: one file per resource in `app/api/`, declared as
  `router = APIRouter(prefix="/<resource>", tags=["<resource>"])` and mounted in `main.py` under `/api/v1`.
- **TypeScript**: `camelCase` for functions/variables; `PascalCase` for components and
  types/interfaces. Files under `lib/` are lowercase-kebab (`api-client.ts`, `types.ts`); component
  files are `PascalCase.tsx`. Import alias `@/*` maps to `frontend/src/*`.
- **Wire format stays snake_case on both sides.** API JSON fields (`company_id`, `source_url`,
  `confidence_overall`) are spelled snake_case in both the Pydantic schemas and the TS interfaces in
  `lib/types.ts` — don't convert to camelCase at the TS boundary. Only non-serialized local function
  parameters use camelCase (e.g. `getTradeFlows(reporterCountry, partnerCountry)`).

## Test expectations

- Backend uses pytest with `asyncio_mode = "auto"` and `testpaths = ["tests"]` (`pyproject.toml`) —
  write `async def test_...()` directly, no `@pytest.mark.asyncio` decorator needed.
- `backend/tests/unit/` and `backend/tests/integration/` both exist but currently have **no test
  files** — there's no existing test in this repo to pattern-match against yet. When adding the
  first ones: unit tests should exercise `logic.py` functions directly (they're framework-agnostic
  by design — see the agent shape in Architecture rules), not through the LangGraph node/graph
  wrapper; integration tests are where anything needing real Postgres/Neo4j/Qdrant/Redis belongs
  (the docker-compose data services).
- `httpx` is in the dev dependency group specifically for FastAPI `TestClient`/async client tests.
- Until real tests exist, `scripts/seed_crawl.py` and `scripts/e2e_query_check.py` are the only
  working end-to-end verification — manual, human-read output, require real API keys, and are not
  part of the pytest suite.
- `ruff check .` and `mypy app` are configured (line-length 100, target py311) but there's no CI
  workflow in this repo wiring them up yet — run both manually before considering backend work done.
