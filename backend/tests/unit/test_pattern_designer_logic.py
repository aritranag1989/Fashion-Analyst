from app.agents.pattern_designer.logic import _format_swatch_catalog, suggest_pattern_specs
from app.agents.pattern_designer.schemas import (
    PatternDesignOutput,
    PatternSpecSuggestion,
    SwatchRoleSuggestion,
)
from app.db.postgres.models import Swatch


class _FakeResult:
    def __init__(self, output: PatternDesignOutput) -> None:
        self.output = output


class _FakeAgent:
    """Stands in for the real PydanticAI Agent - never calls Claude, so this test needs no
    ANTHROPIC_API_KEY, matching the lazy-construction convention's own testability rationale."""

    def __init__(self, output: PatternDesignOutput) -> None:
        self._output = output
        self.last_prompt: str | None = None

    async def run(self, prompt: str) -> _FakeResult:
        self.last_prompt = prompt
        return _FakeResult(self._output)


def _sample_swatches() -> list[Swatch]:
    return [
        Swatch(
            id=1, label="Indigo hemp", hex_color="#1a2b3c", rgb_r=26, rgb_g=43, rgb_b=60,
            photo_storage_path="swatch_photos/a.jpg",
        ),
        Swatch(
            id=2, label="Cream silk", hex_color="#f5f0e6", rgb_r=245, rgb_g=240, rgb_b=230,
            photo_storage_path="swatch_photos/b.jpg",
        ),
    ]


def test_format_swatch_catalog_includes_id_label_hex():
    catalog = _format_swatch_catalog(_sample_swatches())

    assert "id=1" in catalog
    assert "Indigo hemp" in catalog
    assert "#1a2b3c" in catalog
    assert "id=2" in catalog
    assert "#f5f0e6" in catalog


async def test_suggest_pattern_specs_returns_agent_suggestions_unchanged(monkeypatch):
    expected_output = PatternDesignOutput(
        suggestions=[
            PatternSpecSuggestion(
                pattern_type="gingham",
                swatch_roles=[
                    SwatchRoleSuggestion(swatch_id=1, role_index=0),
                    SwatchRoleSuggestion(swatch_id=2, role_index=1),
                ],
                rationale="High-contrast pairing that reads clearly as a check",
            )
        ]
    )
    fake_agent = _FakeAgent(expected_output)
    monkeypatch.setattr(
        "app.agents.pattern_designer.logic._get_designer_agent", lambda: fake_agent
    )

    suggestions = await suggest_pattern_specs(_sample_swatches(), num_suggestions=5)

    assert suggestions == expected_output.suggestions
    assert "5 diverse pattern combinations" in fake_agent.last_prompt
    assert "Indigo hemp" in fake_agent.last_prompt
