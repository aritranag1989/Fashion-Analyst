from app.agents.query_planner.logic import plan_query
from app.graph.state import QueryPlan, QueryState


async def query_planner_node(state: QueryState) -> dict:
    plan_output = await plan_query(state["request_query"])

    plan: QueryPlan = {
        "semantic_query": plan_output.semantic_query,
        "keyword_terms": plan_output.keyword_terms,
        "company_id": state.get("request_company_id"),
        "fabric_tags": plan_output.fabric_tags or state.get("request_fabric_tags", []),
        "needs_graph_traversal": plan_output.needs_graph_traversal,
    }
    return {"plan": plan}
