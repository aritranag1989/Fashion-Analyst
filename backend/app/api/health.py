from fastapi import APIRouter
from sqlalchemy import text

from app.db.postgres.base import engine
from app.db.qdrant_client import get_qdrant_client
from app.db.redis_client import get_redis_client
from app.kg.neo4j_client import get_neo4j_driver

router = APIRouter(tags=["health"])


@router.get("/health")
async def health() -> dict:
    checks: dict[str, str] = {}

    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        checks["postgres"] = "ok"
    except Exception as exc:  # noqa: BLE001 - report status, don't crash the endpoint
        checks["postgres"] = f"error: {exc}"

    try:
        driver = get_neo4j_driver()
        await driver.verify_connectivity()
        checks["neo4j"] = "ok"
    except Exception as exc:  # noqa: BLE001
        checks["neo4j"] = f"error: {exc}"

    try:
        client = get_qdrant_client()
        await client.get_collections()
        checks["qdrant"] = "ok"
    except Exception as exc:  # noqa: BLE001
        checks["qdrant"] = f"error: {exc}"

    try:
        redis = get_redis_client()
        await redis.ping()
        checks["redis"] = "ok"
    except Exception as exc:  # noqa: BLE001
        checks["redis"] = f"error: {exc}"

    overall = "ok" if all(v == "ok" for v in checks.values()) else "degraded"
    return {"status": overall, "checks": checks}
