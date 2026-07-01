from pydantic import BaseModel, Field


class SwatchRoleSuggestion(BaseModel):
    swatch_id: int
    role_index: int = Field(description="0-based position/role within the pattern - order matters")


class PatternSpecSuggestion(BaseModel):
    pattern_type: str = Field(
        description=(
            "One of: gingham, tartan, houndstooth, herringbone, pinstripe, "
            "kasuri, asanoha, seigaiha, ichimatsu"
        )
    )
    swatch_roles: list[SwatchRoleSuggestion] = Field(
        description="Ordered swatch selection. gingham/houndstooth/herringbone/pinstripe/kasuri/"
        "asanoha/seigaiha/ichimatsu need exactly 2 (role_index 0 and 1); tartan needs 2-6 forming "
        "an ordered sett sequence."
    )
    rationale: str = Field(description="One-sentence creative rationale for why this combination works")


class PatternDesignOutput(BaseModel):
    suggestions: list[PatternSpecSuggestion] = Field(default_factory=list)
