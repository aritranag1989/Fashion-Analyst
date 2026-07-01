import json
import re

from anthropic import AsyncAnthropic

from app.agents.industry_research.prompts import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE
from app.agents.industry_research.schemas import CompanyDiscoveryResult
from app.config import get_settings
from app.logging_conf import get_logger

logger = get_logger(__name__)

_JSON_BLOCK_RE = re.compile(r"\{.*\}", re.DOTALL)

FINAL_ANSWER_INSTRUCTION = (
    "\n\nWhen you are done searching, respond with ONLY a single JSON object matching this "
    'shape (no prose before or after): {"candidates": [{"name": str, "website_url": str|null, '
    '"snippet": str, "source_url": str}, ...]}'
)


async def discover_companies(query: str) -> CompanyDiscoveryResult:
    """Uses Claude's server-side web_search tool to find real Japanese textile companies.

    This bypasses PydanticAI deliberately: PydanticAI's cross-provider Agent abstraction does not
    give first-class access to Anthropic's server-side web_search tool, which this agent needs.
    """
    settings = get_settings()
    client = AsyncAnthropic(api_key=settings.anthropic_api_key)

    response = await client.messages.create(
        model=settings.claude_model_standard,
        max_tokens=4096,
        system=SYSTEM_PROMPT,
        tools=[{"type": "web_search_20250305", "name": "web_search", "max_uses": 5}],
        messages=[
            {
                "role": "user",
                "content": USER_PROMPT_TEMPLATE.format(query=query) + FINAL_ANSWER_INSTRUCTION,
            }
        ],
    )

    final_text = "".join(
        block.text for block in response.content if getattr(block, "type", None) == "text"
    )

    match = _JSON_BLOCK_RE.search(final_text)
    if not match:
        logger.warning("industry_research_no_json", query=query, raw=final_text[:500])
        return CompanyDiscoveryResult(candidates=[])

    try:
        data = json.loads(match.group(0))
        return CompanyDiscoveryResult.model_validate(data)
    except (json.JSONDecodeError, ValueError) as exc:
        logger.warning("industry_research_parse_failed", query=query, error=str(exc))
        return CompanyDiscoveryResult(candidates=[])
