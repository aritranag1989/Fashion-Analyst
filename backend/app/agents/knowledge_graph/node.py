from app.agents.knowledge_graph.logic import write_verified_result_to_graph
from app.graph.state import IngestionState
from app.kg.neo4j_client import get_neo4j_driver
from app.logging_conf import get_logger

logger = get_logger(__name__)


async def knowledge_graph_node(state: IngestionState) -> dict:
    driver = get_neo4j_driver()
    errors: list[str] = []

    for verification in state["verification_results"]:
        try:
            await write_verified_result_to_graph(driver, verification)
        except Exception as exc:  # noqa: BLE001
            logger.warning("kg_write_failed", company=verification["payload"].get("name"), error=str(exc))
            errors.append(f"kg_write_failed: {verification['payload'].get('name')}: {exc}")

    return {"errors": errors}
