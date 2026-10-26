# ARGUS implementation status

Last updated: 26 October 2026.

## Implemented and verified locally

- Reproducible Logistic Regression / Random Forest / XGBoost pipeline; validation
  tuning, thresholds and algorithm selection; held-out metrics; chronological
  option; immutable artifacts; actual inference and provenance guards.
- CSV schema/finite/label validation, duplicates, persistent transactions,
  search/sort/filter/pagination, batch scoring, actual stored-data analytics.
- SHAP explanations tested for all three candidate algorithms.
- Cases, transaction links, notes, statuses, priorities, analyst decisions,
  persistence across server restart, history search and JSON reports.
- React analyst pages, CSV import, Laboratory comparison and exports, graph,
  optional Copilot configuration/disabled state, responsive desktop/mobile UI.
- Separate synthetic entity/relationship tables and interactive Cytoscape graph.
- Restricted read-only Ollama context API; enabled path tested using a mock,
  disabled path and unavailable configuration handled honestly.
- Documentation, attribution, MIT license, sample artificial CSV, real synthetic
  evaluation artifact, actual application screenshots, locked dependencies.

## Verification evidence

- 15 pytest tests passed on SQLite, including ML, API, CSV, inference consistency,
  SHAP reconstruction for three algorithms and investigation persistence.
- PostgreSQL 17 native cluster: all 15 tests passed with isolated per-test schemas.
- 3 Vitest component tests passed.
- 4 Playwright browser workflows passed in Chromium: investigation persistence,
  CSV import/error state and updated metrics, all analyst pages, mobile viewport.
- TypeScript, ESLint, Vite production build and Python Ruff/compilation passed.
- npm audit reported zero vulnerabilities after upgrading to patched Vitest.
- Recharts animations disabled after screenshot review caught early empty plots;
  actual desktop/mobile plots visually verified. Browser rerun found an ambiguous
  test selector after creating duplicate-titled cases; selector changed to exact
  newly-created case ID; all 4 browser workflows passed again.
- Docker is unavailable locally. Compose startup is configured as a CI job;
  runtime result is pending GitHub Actions, not claimed as passed yet.

## GitHub

Authenticated account verified: muratkareem. Target was absent; created public
repository https://github.com/muratkareem/argus. First tested backend milestone
committed and pushed (`971d2fc`). Frontend/CI/documentation milestone pending final
checks and push. Credential-pattern scan runs before commits; no datasets,
credentials, local database or model binaries published.

## Explicit limits / remaining work

- Authorized ULB dataset is not supplied. No ULB experimental result claimed;
  authorized download/import and training procedure documented.
- Installed Ollama unavailable: real model integration is unverified.
- PDF reports and synthetic graph entity case links are planned.
- Authentication, authorization, migrations, async ingestion and production
  performance/security are outside this research MVP.
- Complete final browser screenshots, extended PostgreSQL tests, publish verified
  milestone, inspect Actions including Docker, repair failures, record final state.
