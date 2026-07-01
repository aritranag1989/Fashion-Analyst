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
uv run celery -A app.celery_app worker --loglevel=INFO -Q crawl,celery   # add --pool=solo on native Windows (no fork())
uv run celery -A app.celery_app beat --loglevel=INFO
```
Without a running worker, anything that goes through `.delay()` (ingestion trigger, pattern-matrix
generate) enqueues fine but its status stays `PENDING` forever — trigger+poll endpoints and any
frontend polling loop will hang indefinitely, not fail, which can look like a frontend bug.

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
No automated test covers the graphs (or the paid image-gen call) yet (see Test expectations).
These scripts are the real end-to-end proof. Run from `backend/`:
```
uv run python ../scripts/seed_crawl.py "<seed query>"          # ingestion graph once, no Celery - needs ANTHROPIC_API_KEY/VOYAGE_API_KEY
uv run python ../scripts/e2e_query_check.py "<question>"       # query graph, prints cited answer - needs ANTHROPIC_API_KEY/VOYAGE_API_KEY
uv run python ../scripts/e2e_pattern_check.py [<photo> ...]    # swatch->pattern-matrix pipeline + one concept shot - needs ANTHROPIC_API_KEY/OPENAI_API_KEY
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
- `ensure_collections()` (`backend/app/db/qdrant_collections.py`) and `apply_schema()`
  (`backend/app/kg/schema.py`) create the Qdrant collections/payload indexes and Neo4j
  constraints/indexes respectively, and are called from `app/main.py`'s startup lifespan — don't
  remove that, a fresh environment depends on it to get working collections/constraints.
- `infra/k8s/` is an explicitly unvalidated placeholder (see its README) — Phase 1 runs on
  `docker/docker-compose.yml` only. Don't treat the k8s manifests as a working deployment target.
- **The shared async engine (`app/db/postgres/base.py`) must stay on `NullPool`.** Celery tasks
  (`ingestion_tasks.py`, `pattern_tasks.py`) each wrap their work in a fresh `asyncio.run(...)`,
  which creates and destroys an event loop per task. A *real* connection pool would hand the next
  task a connection still bound to the previous task's now-closed loop, crashing with `RuntimeError:
  Event loop is closed` on that task's very first query - the first task after a worker starts
  always works, only the second+ ones fail, which makes this easy to miss in quick manual checks.
  FastAPI/uvicorn doesn't hit this (one persistent event loop for the process's whole lifetime) but
  shares this same engine object, so don't special-case pooling back in for just that path.
- **Agent construction must always be lazy.** Every PydanticAI agent from `make_structured_agent()`
  is built via a module-level `@lru_cache`-decorated getter function (e.g. `_get_planner_agent()`
  in `query_planner/logic.py`, `_get_extraction_agent()` in `verification/logic.py`,
  `_get_designer_agent()` in `pattern_designer/logic.py`), never as a bare module-level assignment.
  A bare assignment runs at import time and makes the whole app fail to boot without a real
  `ANTHROPIC_API_KEY` — this already broke the app once and was fixed; don't reintroduce it.
- **`make_structured_agent()` must build an explicit `AnthropicProvider(api_key=...)`, not the
  `"anthropic:model_name"` string shorthand.** That shorthand makes PydanticAI construct its own
  default provider, which reads `ANTHROPIC_API_KEY` via `os.getenv()` directly — completely
  bypassing this app's `Settings`/`.env`-file loading. Populating `infra/env/.env` alone silently
  did nothing before this was fixed; the key never reached PydanticAI. `industry_research/logic.py`
  (raw `anthropic` SDK) and both embedding providers already passed `api_key=` explicitly and never
  had this problem — only the PydanticAI string-shorthand path did.
- **Not everything multi-step needs a `StateGraph`.** The pattern-mockup pipeline
  (`backend/app/pattern_rendering/pipeline.py`) is deliberately a plain async pipeline, not a third
  LangGraph graph, because it's linear-with-one-fan-out rather than genuinely graph-shaped (no
  multi-branch join, no conditional routing) — see the reasoning in
  `docs/adr/0001-orchestration-framework.md`'s spirit. Only its one LLM-driven step
  (`agents/pattern_designer/`) keeps the 4-file agent shape; the deterministic renderers
  (`pattern_rendering/{gingham,tartan,houndstooth,herringbone,pinstripe,kasuri,asanoha,seigaiha,
  ichimatsu}.py`) are plain functions,
  not agents, since there's no LLM call to wrap.
- **Image generation model names are volatile — verify before trusting one.** `dall-e-3` was
  retired 2026-03-04; the current default is `gpt-image-1` via `images.edit()`
  (`backend/app/imagegen/openai.py`). If you're touching image-gen code, check current OpenAI docs
  rather than assuming a remembered model name still works.
- **No pattern-mockup model's `relationship()` has `cascade` configured** (`Swatch`,
  `PatternMockup`, `PatternSwatchRole`, `ConceptShot` in `db/postgres/models.py`) — deleting a
  parent row without deleting its children first crashes on a NOT NULL FK instead of cascading.
  Both single-row deletion (`delete_swatch` in `api/swatches.py`) and the full-library reset
  (`clear_all_pattern_data` in `pattern_rendering/pipeline.py`, exposed as
  `DELETE /api/v1/patterns/clear-all`) follow the same manual, FK-safe order — delete children,
  commit, then unlink each row's file from disk — rather than one all-or-nothing transaction. Match
  this shape for any new deletion path on these tables instead of relying on ORM cascade.
- **`generate_matrix()`'s requested suggestion count is a request, not a guarantee.** The pattern
  designer prompt asks Claude for `num_llm_suggestions` combinations, but the LLM can return fewer
  (`PatternDesignOutput.suggestions` has no min-length constraint), and suggestions are then
  silently dropped before rendering if they name an unknown `pattern_type`, reference a `swatch_id`
  outside the current library, or use the wrong swatch count for that pattern type
  (`pipeline.py`'s `generate_matrix()`). The first two drop reasons log a warning
  (`generate_matrix_unknown_pattern_type` / `generate_matrix_unknown_swatch_id`); the swatch-count
  mismatch does not log anything — if the rendered count is noticeably below what was requested
  with no warnings in the logs, that silent branch is the first place to look.

## Repo map

```
backend/app/
  agents/<name>/         schemas.py, prompts.py, logic.py, node.py per agent (docs/agents.md has status)
                         includes pattern_designer/ (LLM pattern-combo suggester, no graph wired in)
  graph/                 ingestion_graph.py, query_graph.py, state.py (shared TypedDict states)
  api/                   FastAPI routers: health, search, companies, trade, agents_admin, ingestion,
                         swatches, patterns
  db/postgres/            SQLAlchemy models + async session/engine (system of record + provenance)
  kg/                     Neo4j driver + schema.py (constraints/indexes, example Cypher patterns)
  rag/                    hybrid_search.py, bm25_index.py, chunking.py, embeddings/ (provider ABC)
  trade/                  TradeDataProvider ABC + un_comtrade.py implementation
  pattern_rendering/       color_extraction.py, 9 deterministic pattern renderers, pipeline.py
                          (the swatch/pattern-mockup feature's non-agent core - see Architecture rules)
  imagegen/                ImageGenProvider ABC + openai.py (gpt-image-1) - opt-in AI concept shots
  crawlers/               Playwright crawling, robots.py, scrapy_project/, sources/ (seed list)
  extraction/             html_parser.py, pdf_parser.py, catalog_parser.py
  tasks/                  Celery tasks: ingestion_tasks.py, scheduled.py, pattern_tasks.py
  config.py, celery_app.py, main.py, logging_conf.py
backend/data/             gitignored: swatch_photos/, pattern_tiles/, concept_shots/ (uploaded/generated)
backend/tests/unit/        one file per pattern renderer (pixel-exact assertions) + color extraction
                           + pattern_designer logic (PydanticAI call mocked)
backend/tests/integration/  test_swatch_upload_to_render.py (needs real Postgres)
backend/alembic/versions/  0001_initial_schema.py, 0002_pattern_mockups.py
scripts/                 seed_crawl.py, e2e_query_check.py, e2e_pattern_check.py — manual e2e
                         runners, not pytest-wrapped; fixtures/ has synthetic sample swatch photos
frontend/src/
  app/                   Next.js App Router pages: /, search, companies, companies/[id],
                         companies/compare, graph, map, timeline, trade, patterns, admin
  components/             e.g. components/search/SearchExperience.tsx, components/patterns/*
  lib/                     api-client.ts (fetch wrapper), types.ts (wire-format interfaces)
docker/                  docker-compose.yml + Dockerfile.backend / .worker / .frontend
infra/env/               .env / .env.example (real .env is gitignored — never commit real keys)
infra/k8s/               placeholder manifests, not validated (see Architecture rules)
docs/                    architecture.md, agents.md, data-sources.md, adr/
```

## Naming conventions

- **Python**: `snake_case` for functions/variables/modules; `PascalCase` for Pydantic models and
  SQLAlchemy models; `UPPER_SNAKE_CASE` for module-level constants (`FUZZY_MATCH_THRESHOLD`,
  `MAX_TEXT_CHARS_FOR_EXTRACTION`). Private module-level names are prefixed with `_`, including the
  lazy agent getters (`_get_extraction_agent()`, `_get_designer_agent()`) and query/constant
  literals (`_EGO_NETWORK_QUERY`, `_HOUNDSTOOTH_UNIT`).
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
- `backend/tests/unit/` has the pattern-mockup feature's tests as the first real precedent: one
  file per deterministic renderer asserting **exact pixel values at specific coordinates**
  (`img.getpixel()`), not just "an image object came back" — follow that standard for any new
  deterministic-output code. `backend/tests/integration/` has one file
  (`test_swatch_upload_to_render.py`) needing a real Postgres; it mocks the PydanticAI call rather
  than requiring `ANTHROPIC_API_KEY`. Unit tests exercise `logic.py`/module functions directly
  (framework-agnostic by design), not through a LangGraph node/graph wrapper.
- `httpx` is in the dev dependency group specifically for FastAPI `TestClient`/async client tests
  (see `test_swatch_upload_to_render.py`'s `ASGITransport` usage).
- No automated test calls a real LLM or the real image-gen API (both cost money per call) —
  `scripts/seed_crawl.py`, `scripts/e2e_query_check.py`, and `scripts/e2e_pattern_check.py` are the
  manual, human-read, real-API-key end-to-end proof for those paths instead.
- `ruff check .` and `mypy app` are configured (line-length 100, target py311) but there's no CI
  workflow in this repo wiring them up yet — run both manually before considering backend work done.
