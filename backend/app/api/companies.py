from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.postgres.base import get_session
from app.db.postgres.models import Address, Company, Contact, Product
from app.kg.neo4j_client import get_neo4j_driver

router = APIRouter(prefix="/companies", tags=["companies"])

_EGO_NETWORK_QUERY = """
MATCH (c:Company {company_id: $company_id})
OPTIONAL MATCH (c)-[r]-(neighbor)
RETURN c, collect({relationship: type(r), neighbor_label: labels(neighbor), neighbor: neighbor}) AS edges
"""


@router.get("")
async def list_companies(
    limit: int = 50, offset: int = 0, session: AsyncSession = Depends(get_session)
) -> list[dict]:
    result = await session.execute(select(Company).limit(limit).offset(offset))
    return [
        {"id": c.id, "name": c.name, "company_type": c.company_type, "website_url": c.website_url}
        for c in result.scalars()
    ]


@router.get("/compare")
async def compare_companies(
    ids: str, session: AsyncSession = Depends(get_session)
) -> list[dict]:
    company_ids = [int(i) for i in ids.split(",") if i.strip()]
    result = await session.execute(select(Company).where(Company.id.in_(company_ids)))
    return [
        {
            "id": c.id,
            "name": c.name,
            "company_type": c.company_type,
            "founded_year": c.founded_year,
            "certifications": c.certifications,
            "export_markets": c.export_markets,
        }
        for c in result.scalars()
    ]


@router.get("/{company_id}")
async def get_company(company_id: int, session: AsyncSession = Depends(get_session)) -> dict:
    company = await session.get(Company, company_id)
    if company is None:
        raise HTTPException(status_code=404, detail="Company not found")

    products = (
        await session.execute(select(Product).where(Product.company_id == company_id))
    ).scalars().all()
    contacts = (
        await session.execute(select(Contact).where(Contact.company_id == company_id))
    ).scalars().all()
    addresses = (
        await session.execute(select(Address).where(Address.company_id == company_id))
    ).scalars().all()

    return {
        "id": company.id,
        "name": company.name,
        "name_ja": company.name_ja,
        "company_type": company.company_type,
        "founded_year": company.founded_year,
        "website_url": company.website_url,
        "description": company.description,
        "certifications": company.certifications,
        "products": [{"id": p.id, "name": p.name, "fabric_type": p.fabric_type} for p in products],
        "contacts": [{"type": c.contact_type, "value": c.value} for c in contacts],
        "addresses": [{"city": a.city, "prefecture": a.prefecture, "country": a.country} for a in addresses],
    }


@router.get("/{company_id}/graph")
async def get_company_graph(company_id: int) -> dict:
    driver = get_neo4j_driver()
    async with driver.session() as session:
        result = await session.run(_EGO_NETWORK_QUERY, company_id=company_id)
        record = await result.single()
        if record is None:
            raise HTTPException(status_code=404, detail="Company not found in knowledge graph")
        return {
            "company": dict(record["c"]),
            "edges": [
                {"relationship": e["relationship"], "neighbor_label": e["neighbor_label"], "neighbor": dict(e["neighbor"])}
                for e in record["edges"]
                if e["neighbor"] is not None
            ],
        }
