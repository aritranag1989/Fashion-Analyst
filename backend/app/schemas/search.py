from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    query: str = Field(..., description="Natural-language question from the user")
    top_k: int = Field(10, ge=1, le=50)
    company_id: int | None = None
    fabric_tags: list[str] = Field(default_factory=list)


class Citation(BaseModel):
    source_url: str
    source_type: str
    excerpt: str
    confidence: float
    last_verified_at: str | None = None


class CompanyResult(BaseModel):
    company_id: int | None = None
    name: str | None = None
    address: str | None = None
    country: str | None = None
    website: str | None = None
    contact: str | None = None
    products: list[str] = Field(default_factory=list)


class SearchResponse(BaseModel):
    answer: str
    citations: list[Citation] = Field(default_factory=list)
    companies: list[CompanyResult] = Field(default_factory=list)
    confidence_overall: float = 0.0
    insufficient_data: bool = False
