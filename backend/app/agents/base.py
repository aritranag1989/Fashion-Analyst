from typing import TypeVar

from pydantic import BaseModel
from pydantic_ai import Agent
from pydantic_ai.models.anthropic import AnthropicModel
from pydantic_ai.providers.anthropic import AnthropicProvider

from app.config import get_settings

T = TypeVar("T", bound=BaseModel)


def make_structured_agent(
    output_type: type[T], system_prompt: str, *, high_accuracy: bool = False
) -> Agent:
    """Factory for a PydanticAI agent that returns a validated `output_type` from Claude.

    high_accuracy=True selects the more capable/expensive model (used by Verification and
    Answer Generator); otherwise the cheaper standard model is used (Industry Research triage,
    bulk Knowledge Graph extraction).

    Builds an explicit AnthropicProvider(api_key=...) from our own settings rather than using the
    "anthropic:model_name" string shorthand - that shorthand makes PydanticAI construct its own
    default AnthropicProvider, which reads ANTHROPIC_API_KEY via os.getenv() directly, completely
    bypassing this app's Settings/.env-file loading. Populating infra/env/.env alone was silently
    not enough before this fix; it never reached PydanticAI at all.
    """
    settings = get_settings()
    model_name = (
        settings.claude_model_high_accuracy if high_accuracy else settings.claude_model_standard
    )
    model = AnthropicModel(model_name, provider=AnthropicProvider(api_key=settings.anthropic_api_key))
    return Agent(model=model, output_type=output_type, system_prompt=system_prompt)
