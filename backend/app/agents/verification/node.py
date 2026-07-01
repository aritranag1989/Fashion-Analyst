from app.agents.verification.logic import (
    build_flagged_result,
    extract_fact,
    group_facts_across_documents,
    persist_verified_group,
    score_confidence,
)
from app.config import get_settings
from app.db.postgres.base import AsyncSessionLocal
from app.graph.state import IngestionState, VerificationResult
from app.logging_conf import get_logger

logger = get_logger(__name__)


async def verification_node(state: IngestionState) -> dict:
    settings = get_settings()

    facts_with_docs = []
    for document in state["crawled_documents"]:
        fact = await extract_fact(document)
        if fact is not None:
            facts_with_docs.append((fact, document))

    groups = group_facts_across_documents(facts_with_docs)

    verification_results: list[VerificationResult] = []
    flagged_facts: list[VerificationResult] = []

    async with AsyncSessionLocal() as session:
        for group in groups:
            confidence = score_confidence(group)
            if confidence >= settings.confidence_threshold:
                verification_results.append(await persist_verified_group(session, group, confidence))
            else:
                flagged_facts.append(build_flagged_result(group, confidence))
                logger.info("fact_flagged_for_review", name=group.canonical_name, confidence=confidence)
        await session.commit()

    return {"verification_results": verification_results, "flagged_facts": flagged_facts}
