from datetime import datetime, timezone

from neo4j import AsyncDriver

from app.graph.state import VerificationResult
from app.logging_conf import get_logger

logger = get_logger(__name__)

_MERGE_COMPANY = """
MERGE (c:Company {company_id: $company_id})
SET c.name = $name
"""

_MERGE_LOCATION = """
MATCH (c:Company {company_id: $company_id})
MERGE (city:City {name: $city, country: "Japan"})
MERGE (pref:Prefecture {name: $prefecture})
MERGE (japan:Country {name: "Japan"})
MERGE (city)-[:PART_OF]->(pref)
MERGE (pref)-[:PART_OF]->(japan)
MERGE (c)-[r:LOCATED_IN]->(city)
SET r.source_url = $source_url, r.confidence = $confidence, r.extracted_at = $extracted_at
"""

_MERGE_PRODUCT = """
MATCH (c:Company {company_id: $company_id})
MERGE (p:Product {product_id: $product_id})
SET p.name = $product_name
MERGE (c)-[r:PRODUCES]->(p)
SET r.source_url = $source_url, r.confidence = $confidence, r.extracted_at = $extracted_at
"""

_MERGE_FABRIC = """
MATCH (p:Product {product_id: $product_id})
MERGE (f:Fabric {name: $fabric_name})
MERGE (p)-[r:MADE_OF]->(f)
SET r.source_url = $source_url, r.confidence = $confidence, r.extracted_at = $extracted_at
"""

_MERGE_CERTIFICATION = """
MATCH (c:Company {company_id: $company_id})
MERGE (cert:Certification {name: $cert_name})
MERGE (c)-[r:CERTIFIED_BY]->(cert)
SET r.source_url = $source_url, r.confidence = $confidence, r.extracted_at = $extracted_at
"""


async def write_verified_result_to_graph(driver: AsyncDriver, verification: VerificationResult) -> None:
    payload = verification["payload"]
    company_id = payload.get("company_id")
    if company_id is None:
        return  # nothing to anchor relationships to

    source_url = verification["document_url"]
    confidence = verification["confidence"]
    extracted_at = datetime.now(timezone.utc).isoformat()

    async with driver.session() as session:
        await session.run(_MERGE_COMPANY, company_id=company_id, name=payload.get("name"))

        if payload.get("city"):
            await session.run(
                _MERGE_LOCATION,
                company_id=company_id,
                city=payload["city"],
                prefecture=payload.get("prefecture") or "Unknown",
                source_url=source_url,
                confidence=confidence,
                extracted_at=extracted_at,
            )

        for product_name in payload.get("products", []):
            product_id = f"{company_id}:{product_name}"
            await session.run(
                _MERGE_PRODUCT,
                company_id=company_id,
                product_id=product_id,
                product_name=product_name,
                source_url=source_url,
                confidence=confidence,
                extracted_at=extracted_at,
            )
            for fabric_name in payload.get("fabric_types", []):
                await session.run(
                    _MERGE_FABRIC,
                    product_id=product_id,
                    fabric_name=fabric_name,
                    source_url=source_url,
                    confidence=confidence,
                    extracted_at=extracted_at,
                )

        for cert_name in payload.get("certifications", []):
            await session.run(
                _MERGE_CERTIFICATION,
                company_id=company_id,
                cert_name=cert_name,
                source_url=source_url,
                confidence=confidence,
                extracted_at=extracted_at,
            )

    logger.info("kg_written", company_id=company_id)
