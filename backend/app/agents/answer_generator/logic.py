from functools import lru_cache

from pydantic_ai import Agent

from app.agents.answer_generator.prompts import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE
from app.agents.answer_generator.schemas import AnswerWithCitations
from app.agents.base import make_structured_agent
from app.graph.state import GraphFact, RetrievedChunk


@lru_cache
def _get_answer_agent() -> Agent:
    # Lazy + cached (see verification/logic.py) - the insufficient_data early return below must
    # work without ANTHROPIC_API_KEY, so construction can't happen at import time.
    return make_structured_agent(AnswerWithCitations, SYSTEM_PROMPT, high_accuracy=True)


def _format_context(chunks: list[RetrievedChunk]) -> str:
    if not chunks:
        return "(no verified context available)"
    return "\n\n".join(
        f"- [{chunk['source_url']}] (confidence {chunk['confidence_score']:.2f}): {chunk['chunk_text']}"
        for chunk in chunks
    )


def _format_graph_facts(facts: list[GraphFact]) -> str:
    if not facts:
        return "(none)"
    return "\n".join(
        f"- [{fact['source_url']}] (confidence {fact['confidence']:.2f}): {fact['summary']}"
        for fact in facts
    )


async def generate_answer(
    query: str, chunks: list[RetrievedChunk], graph_facts: list[GraphFact]
) -> AnswerWithCitations:
    if not chunks and not graph_facts:
        return AnswerWithCitations(
            answer="No verified information was found for this query in the current knowledge base.",
            citations=[],
            insufficient_data=True,
        )

    prompt = USER_PROMPT_TEMPLATE.format(
        query=query,
        context_block=_format_context(chunks),
        graph_facts_block=_format_graph_facts(graph_facts),
    )
    result = await _get_answer_agent().run(prompt)
    return result.output
