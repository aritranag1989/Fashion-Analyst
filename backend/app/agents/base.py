from typing import TypeVar

from pydantic import BaseModel
from pydantic_ai import Agent

from app.config import get_settings

T = TypeVar("T", bound=BaseModel)

ANTHROPIC_MODEL_PREFIX = "anthropic:"


def make_structured_agent(
    output_type: type[T], system_prompt: str, *, high_accuracy: bool = False
) -> Agent:
    """Factory for a PydanticAI agent that returns a validated `output_type` from Claude.

    high_accuracy=True selects the more capable/expensive model (used by Verification and
    Answer Generator); otherwise the cheaper standard model is used (Industry Research triage,
    bulk Knowledge Graph extraction).
    """
    settings = get_settings()
    model_name = (
        settings.claude_model_high_accuracy if high_accuracy else settings.claude_model_standard
    )
    return Agent(
        model=f"{ANTHROPIC_MODEL_PREFIX}{model_name}",
        output_type=output_type,
        system_prompt=system_prompt,
    )
