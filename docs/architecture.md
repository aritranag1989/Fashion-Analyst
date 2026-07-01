# Architecture

## Overview

The Japan Fashion & Handloom Intelligence Platform is a multi-agent RAG research platform (not a
chatbot) that builds a searchable, cited, confidence-scored knowledge base of the Japanese
handloom/handwoven textile industry from public sources.

Two LangGraph workflows drive the system:

1. **Ingestion graph** (`backend/app/graph/ingestion_graph.py`): discovers companies, crawls and
   extracts their sites/documents, cross-verifies extracted facts across sources, and - only for
   facts that clear the confidence threshold - embeds them into Qdrant and writes them into Neo4j.
2. **Query graph** (`backend/app/graph/query_graph.py`): plans a query, runs hybrid retrieval
   (vector + BM25 + knowledge graph), re-verifies confidence at query time, and generates a
   citation-only answer - never hallucinating past the verified context.

## Data stores

- **PostgreSQL**: system of record and provenance backbone. Every extracted fact carries a
  `source_id` and `confidence_score_id` (see `backend/app/db/postgres/models.py`).
- **Neo4j**: relationship graph (Company/Product/Fabric/City/Association/TradeFair/etc - see
  `backend/app/kg/schema.py`).
- **Qdrant**: `text_chunks`, `product_catalog_chunks`, `images` (schema-only in Phase 1) - see
  `backend/app/db/qdrant_collections.py`.
- **Redis**: Celery broker/result backend.

## Orchestration framework choice

LangGraph is the primary orchestration framework (see `docs/adr/0001-orchestration-framework.md`
for the full rationale). PydanticAI wraps individual LLM calls inside graph nodes for
schema-validated structured output. LlamaIndex is used only for text-chunking utilities
(`backend/app/rag/chunking.py`) - not for orchestration.

## Anti-hallucination mechanism

This is structural, not just a prompt instruction:
- Every Company/Product/Address/Contact row traces to a `source_id`.
- Every fact has a `ConfidenceScore` computed from cross-source corroboration
  (`backend/app/agents/verification/logic.py`).
- Facts below `settings.confidence_threshold` never reach Qdrant or Neo4j - they only exist in the
  `flagged_facts` review queue.
- The Answer Generator's output schema (`AnswerWithCitations`) has an explicit `insufficient_data`
  field, and returns it immediately (without calling Claude) when no verified context exists.

## Known Phase 1 simplifications (see inline comments at each site for full context)

- Entity resolution / dedup uses in-process fuzzy matching (rapidfuzz) - fine at seed scale, would
  need a proper entity-resolution service at "millions of documents" scale.
- BM25 search rebuilds an in-memory index from a full Qdrant scroll
  (`backend/app/rag/bm25_index.py`) rather than a persistent inverted index.
- Celery runs the whole ingestion pipeline as one task per seed query/source rather than one task
  per agent/queue - see `backend/app/celery_app.py` for the rationale and how to split it later.
- Image Understanding is an inert stub; the `images` Qdrant collection exists but is unpopulated.
