# Api

The current verified implementation is documented in [the diploma report](diploma/07_DEPLOYMENT_GUIDE.md). See [PROGRESS.md](../PROGRESS.md) for execution results and [NEXT_STEPS.md](../NEXT_STEPS.md) for outstanding work. Historical runtime instructions have been retired.

OpenAPI is served at `/docs`. Main operations: POST `/api/v1/predict`, `/predict/batch`, `/predict/explanation`; GET `/health`, `/ready`, `/models`, `/settings`, `/datasets`, `/overview`, `/transactions`; POST `/datasets/upload`, `/datasets/{id}/score`; case, saved-view, graph and search routes retain their documented OpenAPI schemas. All paths use `/api/v1`. Optional Authorization: Bearer header protects operations except health.
