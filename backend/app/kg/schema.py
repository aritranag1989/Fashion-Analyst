"""Neo4j schema setup: node key constraints + indexes for the knowledge graph.

Node labels: Company, Product, City, Prefecture, Country, Association, TradeFair, Fabric,
Certification, Person.

Relationship types (all carry source_url, confidence, extracted_at properties, set by the
Knowledge Graph Agent - see app/agents/knowledge_graph/logic.py):
LOCATED_IN, PART_OF, PRODUCES, MADE_OF, CERTIFIED_BY, MEMBER_OF, EXHIBITED_AT {year},
SUPPLIES_TO, EXPORTS_TO {role}, IMPORTS_FROM {role}, WORKS_AT {role}.
"""

from neo4j import AsyncDriver

CONSTRAINTS = [
    "CREATE CONSTRAINT company_id IF NOT EXISTS FOR (c:Company) REQUIRE c.company_id IS UNIQUE",
    "CREATE CONSTRAINT product_id IF NOT EXISTS FOR (p:Product) REQUIRE p.product_id IS UNIQUE",
    "CREATE CONSTRAINT city_name IF NOT EXISTS FOR (c:City) REQUIRE (c.name, c.country) IS UNIQUE",
    "CREATE CONSTRAINT prefecture_name IF NOT EXISTS FOR (p:Prefecture) REQUIRE p.name IS UNIQUE",
    "CREATE CONSTRAINT country_name IF NOT EXISTS FOR (c:Country) REQUIRE c.name IS UNIQUE",
    "CREATE CONSTRAINT association_id IF NOT EXISTS FOR (a:Association) REQUIRE a.association_id IS UNIQUE",
    "CREATE CONSTRAINT trade_fair_id IF NOT EXISTS FOR (t:TradeFair) REQUIRE t.event_id IS UNIQUE",
    "CREATE CONSTRAINT fabric_name IF NOT EXISTS FOR (f:Fabric) REQUIRE f.name IS UNIQUE",
    "CREATE CONSTRAINT certification_name IF NOT EXISTS FOR (c:Certification) REQUIRE c.name IS UNIQUE",
    "CREATE CONSTRAINT person_id IF NOT EXISTS FOR (p:Person) REQUIRE p.person_id IS UNIQUE",
]

INDEXES = [
    "CREATE INDEX company_name_idx IF NOT EXISTS FOR (c:Company) ON (c.name)",
    "CREATE INDEX product_name_idx IF NOT EXISTS FOR (p:Product) ON (p.name)",
]


async def apply_schema(driver: AsyncDriver) -> None:
    async with driver.session() as session:
        for statement in CONSTRAINTS + INDEXES:
            await session.run(statement)


# Example Cypher patterns the Knowledge Graph Agent writes and the query graph reads:
#
# Prefecture-scoped export claims:
#   MATCH (c:Company)-[e:EXPORTS_TO]->(country:Country {name: "India"})
#   MATCH (c)-[:LOCATED_IN]->(:City)-[:PART_OF]->(pref:Prefecture {name: $prefecture})
#   RETURN c, e
#
# Supply-chain traversal (up to 3 hops):
#   MATCH path = (c:Company {company_id: $id})-[:SUPPLIES_TO*1..3]->(downstream:Company)
#   RETURN path
#
# Shared-trade-fair co-exhibitors:
#   MATCH (a:Company)-[:EXHIBITED_AT]->(fair:TradeFair)<-[:EXHIBITED_AT]-(b:Company)
#   WHERE a.company_id <> b.company_id
#   RETURN fair, a, b
