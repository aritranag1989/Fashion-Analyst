from dataclasses import dataclass, field
from functools import lru_cache

from pydantic_ai import Agent
from rapidfuzz import fuzz
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.base import make_structured_agent
from app.agents.verification.prompts import EXTRACTION_SYSTEM_PROMPT, EXTRACTION_USER_TEMPLATE
from app.agents.verification.schemas import ExtractedCompanyFact
from app.db.postgres.models import (
    Address,
    Company,
    ConfidenceScore,
    Contact,
    Product,
)
from app.graph.state import CrawledDocument, VerificationResult
from app.logging_conf import get_logger

logger = get_logger(__name__)

FUZZY_MATCH_THRESHOLD = 88
MAX_TEXT_CHARS_FOR_EXTRACTION = 12000


@lru_cache
def _get_extraction_agent() -> Agent:
    # Lazy + cached so importing this module never requires ANTHROPIC_API_KEY - only actually
    # running extraction does (e.g. a Qdrant-only or Postgres-only smoke boot must not need it).
    return make_structured_agent(
        ExtractedCompanyFact, EXTRACTION_SYSTEM_PROMPT, high_accuracy=True
    )


@dataclass
class FactGroup:
    canonical_name: str
    fact: ExtractedCompanyFact
    source_urls: list[str] = field(default_factory=list)
    source_ids: list[int] = field(default_factory=list)


async def extract_fact(document: CrawledDocument) -> ExtractedCompanyFact | None:
    if not document["text"].strip():
        return None
    text = document["text"][:MAX_TEXT_CHARS_FOR_EXTRACTION]
    result = await _get_extraction_agent().run(
        EXTRACTION_USER_TEMPLATE.format(url=document["url"], text=text)
    )
    fact = result.output
    return fact if fact.mentions_company and fact.name else None


def group_facts_across_documents(
    facts_with_docs: list[tuple[ExtractedCompanyFact, CrawledDocument]],
) -> list[FactGroup]:
    """Fuzzy-matches company names across documents so the same company found on multiple pages
    corroborates itself (raising confidence) instead of creating duplicate records."""
    groups: list[FactGroup] = []

    for fact, document in facts_with_docs:
        match = next(
            (g for g in groups if fuzz.token_sort_ratio(g.canonical_name, fact.name) >= FUZZY_MATCH_THRESHOLD),
            None,
        )
        if match:
            match.source_urls.append(document["url"])
            match.source_ids.append(document["source_id"])
            # merge sparse fields from the new fact into the canonical one
            for field_name in fact.model_fields:
                if not getattr(match.fact, field_name) and getattr(fact, field_name):
                    setattr(match.fact, field_name, getattr(fact, field_name))
        else:
            groups.append(
                FactGroup(
                    canonical_name=fact.name,
                    fact=fact,
                    source_urls=[document["url"]],
                    source_ids=[document["source_id"]],
                )
            )

    return groups


def score_confidence(group: FactGroup) -> float:
    distinct_sources = len(set(group.source_ids))
    base = 0.5
    corroboration_bonus = min(0.4, 0.15 * (distinct_sources - 1))
    return round(min(1.0, base + corroboration_bonus), 2)


async def find_existing_company(session: AsyncSession, name: str) -> Company | None:
    result = await session.execute(select(Company))
    for company in result.scalars():
        if fuzz.token_sort_ratio(company.name, name) >= FUZZY_MATCH_THRESHOLD:
            return company
    return None


def build_flagged_result(group: FactGroup, confidence: float) -> VerificationResult:
    """Below-threshold facts are never written to Company/Product/etc - they only appear in the
    review queue (flagged_facts) so a human or a future re-verification pass can promote them."""
    return VerificationResult(
        entity_type="company",
        payload={"name": group.fact.name},
        confidence=confidence,
        verification_method="cross_source_name_corroboration",
        corroborating_source_urls=group.source_urls,
        document_url=group.source_urls[0],
    )


async def persist_verified_group(session: AsyncSession, group: FactGroup, confidence: float) -> VerificationResult:
    """Only call this for groups whose confidence already cleared settings.confidence_threshold."""
    fact = group.fact
    company = await find_existing_company(session, group.canonical_name)

    if company is None:
        company = Company(
            name=fact.name,
            name_ja=fact.name_ja,
            company_type=fact.company_type,
            founded_year=fact.founded_year,
            description=fact.description,
            certifications=fact.certifications,
            source_id=group.source_ids[0],
        )
        session.add(company)
        await session.flush()

    confidence_row = ConfidenceScore(
        entity_type="company",
        entity_id=company.id,
        score=confidence,
        verification_method="cross_source_name_corroboration",
        verifier_agent="verification_agent",
        corroborating_source_ids=list(set(group.source_ids)),
    )
    session.add(confidence_row)
    await session.flush()
    company.confidence_score_id = confidence_row.id

    for product_name in fact.products:
        session.add(
            Product(
                company_id=company.id,
                name=product_name,
                fabric_type=fact.fabric_types[0] if fact.fabric_types else None,
                technique=fact.techniques[0] if fact.techniques else None,
                certifications=fact.certifications,
                source_id=group.source_ids[0],
            )
        )

    for email in fact.emails:
        session.add(Contact(company_id=company.id, contact_type="email", value=email, source_id=group.source_ids[0]))
    for phone in fact.phones:
        session.add(Contact(company_id=company.id, contact_type="phone", value=phone, source_id=group.source_ids[0]))

    if fact.address_text or fact.city:
        session.add(
            Address(
                company_id=company.id,
                line1=fact.address_text,
                city=fact.city,
                prefecture=fact.prefecture,
                country="Japan",
                source_id=group.source_ids[0],
            )
        )

    return VerificationResult(
        entity_type="company",
        payload={
            "company_id": company.id,
            "name": company.name,
            "products": fact.products,
            "fabric_types": fact.fabric_types,
            "techniques": fact.techniques,
            "certifications": fact.certifications,
            "city": fact.city,
            "prefecture": fact.prefecture,
        },
        confidence=confidence,
        verification_method="cross_source_name_corroboration",
        corroborating_source_urls=group.source_urls,
        document_url=group.source_urls[0],
    )
