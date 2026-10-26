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

1. Extend the completed authorized ULB stratified/chronological experiments with
   repeated seeds, confidence intervals and independent external validation.
2. Calibration and expected-cost policies with explicit validated assumptions.
3. Broader tuning, feature stability, temporal drift and external data evaluation.
4. Reproducibility manifests for externally supplied datasets and stronger model
   registry integrity checks.

## Product next

1. Authentication, authorization, migrations, audit events, and deletion/retention
   policies before any multi-user or sensitive-data deployment.
2. Chunked ingestion, background scoring jobs, and SQL-aggregated dashboard
   metrics for larger volumes; profiling with the authorized full dataset.
3. Custom-schema mappings; graph entity case links and neighborhood traversal are now implemented.
4. PDF reporting; current reports use interoperable CSV and JSON.
5. Extend the verified qwen2.5:7b integration with additional models and factual
   evaluation. Structured citation IDs and read-only boundaries are validated;
   hallucination prevention is not guaranteed.
6. More extensive browser accessibility, keyboard/focus management, and device
   coverage. Current testing covers Chromium desktop and a narrow mobile viewport.
