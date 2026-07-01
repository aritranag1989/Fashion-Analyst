from app.agents.pattern_designer.logic import suggest_pattern_specs


async def pattern_designer_node(state: dict) -> dict:
    """Not wired into any StateGraph today - this feature uses a direct pipeline
    (app.pattern_rendering.pipeline.generate_matrix), not LangGraph, since it's linear with one
    fan-out rather than genuinely graph-shaped. Kept in agent shape for consistency and in case a
    future graph wants to reuse this as a node, matching image_understanding_node's precedent."""
    suggestions = await suggest_pattern_specs(
        state["available_swatches"], state.get("num_suggestions", 20)
    )
    return {"pattern_suggestions": suggestions}
