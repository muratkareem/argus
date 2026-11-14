# ARGUS checkpoint — 14 November 2026

Branch: `development/diploma-ready`. All prior ML, Frontend and Data Security agent changes recovered; no overwrite or discarded work. No dataset redownload or repeated ULB training during recovery. No changes pushed. Last implementation commit before final verification checkpoint: `03edbe9`; find this checkpoint's exact hash with `git log -1 -- PROGRESS.md`.

## Completed

- Removed all language-model runtime routes/module/config/UI and obsolete service instructions/assets. Conventional ML and SHAP remain.
- LR/RF/XGBoost: strict schemas, train-only preprocessing, reproducible stratified/chronological partitions, validation-only model/threshold selection, observed audits, ROC/PR/FNR/Brier/calibration and illustrative threshold cost profiles.
- Trusted versioned artifacts, checksum/atomic activation/concurrent loading; bounded cached SHAP with exact output space and additivity validation.
- Single and vectorized batch API (1000 maximum), request thresholds, model/risk metadata, direct SHAP, readiness, optional API key, sanitized validation/SQL errors, request IDs/logging.
- Atomic bounded imports, conflicting-label protection, activation-race rollback, SQLite integrity/WAL, additive migration/indexes; bounded rescoring and graph queries, filter/search/view hardening.
- Frontend feature-schema form, probability/threshold/explanation workflow, measured diagnostics, system/key configuration, lazy graph, observed labels separate from review flags, persisted analyst investigations.
- Native bootstrap now migrates and reuses existing demo rows/models. Docker builds and starts successfully. Ten English diploma documents, current API/architecture pointers and measured evidence committed.

## Architecture/files

FastAPI modular monolith: backend/app/{main,config,db,data,intelligence,ml}.py. SQLAlchemy SQLite/PostgreSQL; offline sklearn/XGBoost pipelines; server-owned versioned joblib/JSON; on-demand SHAP. React/TypeScript/Vite with Recharts and lazy Cytoscape; frontend/src/pages contains prediction, diagnostics, system and analyst pages. See docs/diploma/02_SYSTEM_ARCHITECTURE.md. Tests backend/tests and frontend/{src,e2e}. Full modified-file inventory: `git diff --stat c7a4691..HEAD`; focused history: docs/DEVELOPMENT_LOG.md plus git log.

## Final verification

- SQLite 78 passed/5.36s; PostgreSQL17 78 passed/7.41s.
- Ruff lint/format and compileall pass. Frontend lint/typecheck/build pass; 12 unit tests in five files pass.
- Final clean Chrome E2E 12/12 passed/13.9s. Refreshed actual screenshots preserved; mobile layout visually reviewed.
- Final isolated Docker three-service build/start and frontend/health/readiness/600-scored-row/observed-label checks pass. Native bootstrap twice reused600 records. Test containers and native PostgreSQL test cluster stopped; volumes/data retained.
- Dependency audit: nine moderate development-tool advisories; zero high/critical. Starlette/httpx deprecation warning remains.
- Evidence: docs/research/diploma-verification.json and diploma-compose-smoke.json.

## Measured results

Official ULB284807 original rows/492 positives →283726 deduplicated/473 positives. Stratified validation selects XGBoost: test precision.9474, recall.7579, F1.8421, AP.8069, ROC-AUC.9793. Chronological selects Logistic Regression: precision.9423, recall.6622, F1.7778, AP.7475, ROC-AUC.9818. Full reports/source checksum preserved in docs/research/diploma-ulb-*.json.

60k-row isolated import benchmark:20.335→15.068s; peak traced Python allocations264.012→55.947MiB. Final warm in-process10k-row HTTP p95: health1.700ms, prediction5.959ms, query2.743ms, overview13.464ms;1000-record batch38.067ms. These are workstation/concurrency-one measurements, not real-bank guarantees; validations add overhead versus baseline. Full methodology and limitations: docs/diploma/05_EXPERIMENTAL_RESULTS.md.

## Preserved local state

.venv and frontend/node_modules installed. Raw authorized CSV data/private/creditcard.csv SHA25676274b691b16a6c49d3f159c883398e03ccd6d1ee12d9d8ee38f4b4b98551a89; do not download again. Existing full ULB artifacts .local/ulb-stratified and .local/ulb-chronological; do not repeat training. Independent synthetic E2E workspace .local/e2e.db/.local/e2e-artifacts. Original code archive .local/baseline, benchmark model .local/baseline-models. Native PostgreSQL cluster .local/postgres-data stopped. Compose project argus-diploma volumes preserved, private env/port override at .local/compose.env and .local/compose.override.yml. No secrets/datasets/model binaries committed.

## Remaining limitations / exact next work

Core diploma demonstration is verified; broader research claims remain partial. Review publisher dataset license terms before redistribution/use; validate calibration and multiple seeds independently before deployment claims; benchmark full-dataset/concurrent API and browser initial load; optionally add global SHAP summary beyond model-native importance. Nine moderate dev-tool advisories need a safe dependency compatibility update; do not force the audit's proposed downgrade blindly. Large exports and some case lists still materialize results; measure before adding complexity. Optional duplicate-audit optimization was benchmarked but NOT implemented; .local/ml-audit-benchmark.json is prototype evidence only. No production compliance/identity/per-user authorization/TLS guarantee. See NEXT_STEPS.md and docs/diploma/10_REQUIREMENTS_TRACEABILITY.md.
