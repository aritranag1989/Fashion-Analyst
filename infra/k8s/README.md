# Kubernetes manifests - PLACEHOLDER

These manifests are representative starting points for a future cloud deployment. They have
**not** been applied to or validated against a real cluster. Phase 1 runs entirely on local Docker
Compose (`docker/docker-compose.yml`) - see the top-level plan/docs for why.

Known gaps before these are production-ready:
- No StatefulSets/PVCs for Postgres, Neo4j, or Qdrant (Phase 1 assumes managed/hosted equivalents
  or a separate data-layer decision once a cloud provider is chosen).
- No resource requests/limits, HPA, PodDisruptionBudgets, or NetworkPolicies.
- `fashion-analyst-env` Secret is referenced but not defined here - populate it from
  `infra/env/.env.example` via your cluster's secret management (do not commit real secrets).
- No Ingress/TLS configuration.
