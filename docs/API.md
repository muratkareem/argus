# Api

The current verified implementation is documented in [the diploma report](diploma/07_DEPLOYMENT_GUIDE.md). See [PROGRESS.md](../PROGRESS.md) for execution results and [NEXT_STEPS.md](../NEXT_STEPS.md) for outstanding work. Historical runtime instructions have been retired.

OpenAPI is served at `/docs`. Main operations: POST `/api/v1/predict`, `/predict/batch`, `/predict/explanation`; GET `/health`, `/ready`, `/models`, `/settings`, `/datasets`, `/overview`, `/transactions`; POST `/datasets/upload`, `/datasets/{id}/score`; case, saved-view, graph and search routes retain their documented OpenAPI schemas. All paths use `/api/v1`. Optional Authorization: Bearer header protects operations except health.

`GET /api/v1/benchmarks` returns `{datasets, experiments, report_errors,
interpretation}` from server-owned research JSON. Datasets identify `real` versus
`synthetic` and `evaluated`, `access_required` or `not_evaluated` status. Experiments
retain model metrics/partitions and include optional conditional Wilson intervals.
Malformed or incomplete reports are excluded with errors rather than replaced by
placeholder results. `/models` and every production ULB prediction contract remain
unchanged. This endpoint supports external evaluation, not external-model
activation or cross-dataset inference. Configuration: `ARGUS_BENCHMARK_DIR` points
to the research directory; the default is bundled in native and Docker deployments.
