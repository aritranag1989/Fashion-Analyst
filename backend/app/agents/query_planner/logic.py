from functools import lru_cache

from pydantic_ai import Agent

from app.agents.base import make_structured_agent
from app.agents.query_planner.prompts import SYSTEM_PROMPT
from app.agents.query_planner.schemas import QueryPlanOutput


@lru_cache
def _get_planner_agent() -> Agent:
    # Lazy + cached (see verification/logic.py) so importing this module doesn't require
    # ANTHROPIC_API_KEY.
    return make_structured_agent(QueryPlanOutput, SYSTEM_PROMPT)


async def plan_query(query: str) -> QueryPlanOutput:
    result = await _get_planner_agent().run(query)
    return result.output
