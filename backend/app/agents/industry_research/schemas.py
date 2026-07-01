from pydantic import BaseModel, Field


class CompanyCandidate(BaseModel):
    name: str
    website_url: str | None = None
    snippet: str = Field(description="One or two sentences on why this company matched the query")
    source_url: str = Field(description="The page the candidate was found on/via")


class CompanyDiscoveryResult(BaseModel):
    candidates: list[CompanyCandidate]
