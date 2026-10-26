# Roadmap

## Working MVP

- Three-model reproducible training, held-out metrics, versioned real inference.
- CSV validation, duplicates, storage, filters, search, sorting, pagination.
- Backend-driven analytics, ML Laboratory, SHAP, CSV/JSON exports.
- Persisted cases, transaction links, status, priority, notes, analyst decisions.
- Separate interactive synthetic relational graph.
- Optional read-only Ollama context API, disabled by default.
- PostgreSQL Compose architecture, SQLite local fallback, automated tests and CI.

## Research next

1. Authorized ULB dataset run; publish actual metrics and environment alongside
   stratified and chronological evaluations and confidence intervals.
2. Calibration and expected-cost policies with explicit validated assumptions.
3. Broader tuning, feature stability, temporal drift and external data evaluation.
4. Reproducibility manifests for externally supplied datasets and stronger model
   registry integrity checks.

## Product next

1. Authentication, authorization, migrations, audit events, and deletion/retention
   policies before any multi-user or sensitive-data deployment.
2. Chunked ingestion, background scoring jobs, and SQL-aggregated dashboard
   metrics for larger volumes; profiling with the authorized full dataset.
3. Custom-schema mappings; explicit case links for synthetic graph entities.
4. PDF reporting; current reports use interoperable CSV and JSON.
5. Installed-Ollama integration verification, structured citations and response
   validation. The enabled HTTP path is mocked in tests; hallucination prevention
   is not guaranteed.
6. More extensive browser accessibility, keyboard/focus management, and device
   coverage. Current testing covers Chromium desktop and a narrow mobile viewport.
