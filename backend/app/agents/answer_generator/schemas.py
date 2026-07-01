from pydantic import BaseModel, Field


class CitationOutput(BaseModel):
    source_url: str
    excerpt: str = Field(description="The specific sentence/fact from the source backing the claim")


class AnswerWithCitations(BaseModel):
    answer: str = Field(
        description="The answer to the user's question, grounded only in the provided context. "
        "If the context is empty or insufficient, this must clearly state that no verified data "
        "was found rather than guessing."
    )
    citations: list[CitationOutput] = Field(default_factory=list)
    insufficient_data: bool = Field(
        description="True if the provided context did not contain enough verified information to "
        "answer the question"
    )
