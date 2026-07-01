from pydantic import BaseModel, Field


class ExtractedCompanyFact(BaseModel):
    mentions_company: bool = Field(
        description="True if this page describes a specific company/organization, not a generic portal page"
    )
    name: str | None = None
    name_ja: str | None = None
    company_type: str | None = Field(
        None, description="e.g. weaver, dyer, cooperative, association, exporter"
    )
    founded_year: int | None = None
    description: str | None = None
    products: list[str] = Field(default_factory=list)
    fabric_types: list[str] = Field(default_factory=list, description="e.g. silk, cotton, hemp, indigo")
    techniques: list[str] = Field(default_factory=list, description="e.g. kasuri, shibori, sashiko")
    certifications: list[str] = Field(default_factory=list)
    emails: list[str] = Field(default_factory=list)
    phones: list[str] = Field(default_factory=list)
    address_text: str | None = None
    city: str | None = None
    prefecture: str | None = None
