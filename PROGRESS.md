# ARGUS development checkpoint

Date: 14 November 2026 (Asia/Almaty). Branch: `development/diploma-ready`.
Recovered commit: `239fb89` (36 local development commits since `c7a4691`). No changes pushed. The interrupted emergency checkpoint left a clean worktree; this file and NEXT_STEPS.md had not been created.

## Completed implementation

- ML agent: strict schema/probability validation; LR/RF/XGBoost comparison; validation-only thresholds and illustrative costs; ROC/FNR/Brier/calibration; dataset audits; warm model latency; artifact checksum verification, atomic activation, concurrent model caching; bounded SHAP cache with exact output space and additivity checks; reproducibility tests. Eight commits, ending `b137477`.
- Frontend agent: removed generative assistant; actual 30-feature prediction form, request thresholds and SHAP; model diagnostics and system/dataset info; optional session API key; lazy graph engine; unit and browser coverage. Seven commits, ending `7cd8ed0`.
- Data Security agent: atomic bounded imports; duplicate-label rejection; observed dataset audit; SQLite FK/WAL/busy timeout; additive migrations and indexes; bounded graph SQL; finite filters, literal search, saved-view pagination; concurrent import/model activation rollback. Ten commits, ending `a46391c`.
- Integration: removed backend generation routes/module/config; single and vectorized batch prediction (maximum 1000); direct explanation; optional Bearer API key; safe validation errors and request logging; model readiness; worker CSV ingestion; bounded rescoring. Focused local commits throughout.
- Completed official ULB stratified and chronological experiments are preserved in `docs/research/diploma-ulb-*.json`. Do not repeat or redownload. Raw CSV is ignored at `data/private/creditcard.csv`, SHA256 `76274b691b16a6c49d3f159c883398e03ccd6d1ee12d9d8ee38f4b4b98551a89`. Artifacts: `.local/ulb-stratified` and `.local/ulb-chronological`. 284807 original rows, 283726 deduplicated, 473 remaining frauds. Validation selected XGBoost (stratified) and Logistic Regression (chronological).

## Architecture and changed files

FastAPI modular monolith (`backend/app/{main,config,db,data,intelligence,ml}.py`), SQLAlchemy SQLite/PostgreSQL, offline sklearn/XGBoost pipelines and trusted versioned joblib, on-demand SHAP. React/TypeScript/Vite pages in `frontend/src/pages/`; Recharts and lazy Cytoscape. No runtime language-model dependency. Tests in backend/tests and frontend/{src,e2e}. See `git diff --stat c7a4691..HEAD` for exhaustive changed-file inventory and `git log c7a4691..HEAD` for agent changes. Raw datasets, binaries, caches and database state remain ignored.

## Verified before interruption

- `.venv/bin/pytest -q`: 77 passed (5.38s), SQLite.
- `ARGUS_TEST_DATABASE_URL=postgresql+psycopg://main@127.0.0.1:55432/postgres .venv/bin/pytest -q`: 77 passed (8.77s), PostgreSQL17 isolated cluster.
- Ruff lint/format and compileall pass. `npm run lint`, `npm test` (12), `npm run build` pass.
- Browser: 11/12 initially; remaining assertion corrected, targeted rerun1/1 passed. Final full rerun pending.
- Measured 60k synthetic import with fake vector predictor:20.335→15.068s; peak tracemalloc264.012→55.947MiB. Not whole-process RSS or full ML throughput.
- Original API benchmark at docs/research/diploma-baseline-api.json. Optimized comparison pending.

## Known limitations and pending work

README/architecture/API/status docs contain obsolete generative-service instructions and historical screenshots. Required ten docs/diploma documents remain missing. Nine moderate development-only npm advisories were reported; no fix applied. Starlette/httpx TestClient deprecation warning remains. Full Docker stack not yet verified. Existing bootstrap uses create_all rather than migrate and may create empty import records on repeat. Overview ground-truth counts need review. No production authorization or calibration guarantee. Optional duplicate-audit prototype benchmark exists at .local/ml-audit-benchmark.json but optimization was NOT implemented; do not claim its gains.

## Preserved environment and next actions

Dependencies installed in .venv/frontend/node_modules. Isolated E2E DB/model at .local/e2e.db and .local/e2e-artifacts. PostgreSQL cluster .local/postgres-data was started on loopback55432; emergency shutdown was rejected because usage exhausted, so check readiness before reusing. Docker Desktop was started successfully through its nested application; check docker info. No Compose stack was created. No important uncommitted code was lost.

Follow NEXT_STEPS.md. Last implementation commit at checkpoint: `239fb89`; checkpoint documentation commit is discoverable with `git log -1 -- PROGRESS.md` (a file cannot contain its own commit hash).
