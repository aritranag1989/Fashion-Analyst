from app.agents.answer_generator.logic import generate_answer
from app.graph.state import QueryState


async def answer_generator_node(state: QueryState) -> dict:
    result = await generate_answer(state["request_query"], state["verified_chunks"], state["graph_facts"])

    confidence_overall = (
        sum(c["confidence_score"] for c in state["verified_chunks"]) / len(state["verified_chunks"])
        if state["verified_chunks"]
        else 0.0
    )

    return {
        "answer": result.answer,
        "citations": [c.model_dump() for c in result.citations],
        "confidence_overall": round(confidence_overall, 2),
        "insufficient_data": result.insufficient_data,
    }
