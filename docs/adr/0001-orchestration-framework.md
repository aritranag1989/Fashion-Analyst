# ADR 0001: Orchestration framework

## Decision

LangGraph is the primary orchestration framework for both the ingestion pipeline and the query
(RAG) pipeline.

## Context

The spec called for evaluating LangGraph, CrewAI, and PydanticAI (plus LlamaIndex for RAG). The
system is a graph of specialized agents with conditional routing (below-confidence-threshold facts
route to a review queue instead of continuing) and needs durable, resumable state for long-running
crawls across potentially thousands of pages.

## Alternatives considered

- **CrewAI**: optimized for role-playing "crews" with implicit delegation between agents. Good fit
  for loosely-specified collaborative tasks; a weaker fit here because this pipeline is a
  deterministic, mostly-DAG-shaped process where every step's confidence/citations must be
  traceable - not an emergent conversation between agents. Rejected.
- **PydanticAI**: excellent for a single agent call with strict structured/validated output, but it
  is not a multi-agent graph/orchestration framework. Used *inside* LangGraph nodes instead (e.g.
  `backend/app/agents/verification/logic.py`, `backend/app/agents/query_planner/logic.py`) for
  exactly that purpose.
- **Using all of LangGraph + CrewAI + PydanticAI + LlamaIndex as parallel orchestration layers**:
  redundant for a system that is fundamentally one DAG (ingestion) and one DAG (query). Rejected in
  favor of one orchestrator with narrow, well-scoped uses of the others.

## Where the others still fit

- **PydanticAI**: structured-output wrapper inside LangGraph nodes (`backend/app/agents/base.py`
  provides the shared factory).
- **LlamaIndex**: text-chunking utility only (`backend/app/rag/chunking.py`) - not used for its own
  agent/workflow abstractions.

## One documented exception

`backend/app/agents/industry_research/logic.py` calls the raw `anthropic` SDK directly instead of
going through the PydanticAI wrapper, because it specifically needs Claude's server-side
`web_search_20250305` tool, which PydanticAI's cross-provider `Agent` abstraction does not expose
as a first-class feature. This is a deliberate, narrow exception - not a pattern to generalize.
