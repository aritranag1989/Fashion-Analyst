from functools import lru_cache

from pydantic_ai import Agent

from app.agents.base import make_structured_agent
from app.agents.pattern_designer.prompts import SYSTEM_PROMPT
from app.agents.pattern_designer.schemas import PatternDesignOutput, PatternSpecSuggestion
from app.db.postgres.models import Swatch


@lru_cache
def _get_designer_agent() -> Agent:
    # Lazy + cached (see verification/query_planner/answer_generator logic.py) so importing this
    # module never requires ANTHROPIC_API_KEY - only actually calling suggest_pattern_specs() does.
    return make_structured_agent(PatternDesignOutput, SYSTEM_PROMPT)


def _format_swatch_catalog(swatches: list[Swatch]) -> str:
    return "\n".join(f"id={s.id} label={s.label!r} hex={s.hex_color}" for s in swatches)


async def suggest_pattern_specs(
    available_swatches: list[Swatch], num_suggestions: int = 20
) -> list[PatternSpecSuggestion]:
    catalog = _format_swatch_catalog(available_swatches)
    result = await _get_designer_agent().run(
        f"Available swatches:\n{catalog}\n\nSuggest {num_suggestions} diverse pattern combinations."
    )
    return result.output.suggestions
