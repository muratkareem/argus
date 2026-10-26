# ARGUS implementation status

Updated: 26 October 2026. Functional MVP implemented and published at
https://github.com/muratkareem/argus.

## Working modules

- Actual ULB pipeline and synthetic fixtures: Logistic Regression, Random Forest,
  XGBoost; validation tuning/threshold/algorithm selection, untouched test metrics,
  duplicate analysis, stratified and chronological splits, trusted serialization,
  provenance guards and actual inference. SHAP reconstruction verified for all
  three algorithms.
- CSV import (192 MiB bounded upload supports the official full ULB file), error
  reporting, duplicate detection, PostgreSQL persistence, batch inference,
  pagination/search/filter/sort and CSV/JSON transaction export.
- SQL-aggregated analytics, actual stored-data dashboard, transaction details,
  SHAP, saved experiment comparison/PR curves/confusion matrices/importance/export.
- Persisted investigations, case/transaction links, notes, priorities, statuses,
  analyst decisions, history search, dated JSON reports, restart persistence.
- Separate SQL-backed synthetic relational graph with selection, zoom/pan,
  type highlighting and entity details. No inferred ULB relationships.
- Optional local Ollama read-only evidence API, disabled by default, graceful
  unavailable state. Enabled HTTP response path is mocked in tests.
- React/TypeScript/Vite/Tailwind analyst workspace, all navigation pages,
  responsive desktop/mobile screenshots, loading/error/empty states.
- Locked dependencies, MIT license, candidate-source review and attribution,
  README, architecture, ML methodology, datasets, API and roadmap documentation.
- Non-root API Docker image, PostgreSQL + Nginx Compose stack, GitHub Actions.

## Actual benchmark evidence

Official Kaggle GET download succeeded without credentials. CSV stays ignored at
`data/private/creditcard.csv`; checksum/source metadata is tracked in
`docs/research/ulb-source.json`. No full dataset or model binary is published.

- Original: 284,807 rows. Removed 1,081 duplicate feature rows; 283,726 unique rows,
  473 frauds. Both full-data experiments completed successfully.
- Stratified: XGBoost selected on validation AP. Untouched test: 56,746 rows / 95
  frauds; precision .9474, recall .7579, F1 .8421, AP .8069, ROC-AUC .9793.
- Chronological: Logistic Regression selected on validation AP. Untouched test:
  56,746 rows / 74 frauds; precision .9423, recall .6622, F1 .7778, AP .7475,
  ROC-AUC .9818. All candidates' results are retained; no test-based reselection.
- Exact parameters, thresholds, confusion matrices, PR curves, partitions, hashes,
  runtime and environment are in the two ULB reports under `docs/research/`.
- Synthetic experiment is retained and clearly labeled separately.

## Executed verification

- 16 pytest tests passed on SQLite and 16 on PostgreSQL 17, including API/CSV,
  ML smoke, inference consistency, three-algorithm SHAP and case persistence.
- Ruff lint/format and Python compile checks passed.
- 3 Vitest component tests, ESLint/TypeScript and Vite production build passed.
- npm audit: zero reported vulnerabilities after patched Vitest upgrade.
- 4 Playwright browser workflows passed on SQLite and PostgreSQL-backed demo:
  imports/errors/updated stats, investigation notes/decisions/status persistence,
  exports, model comparison, graph, disabled Copilot, settings, mobile viewport.
- Actual full ULB HTTP upload verified: imported/scored 283,726 rows, skipped
  1,081 duplicates. Actual ULB single prediction matched stored batch inference.
- Local PostgreSQL workspace: 284,366 scored records (283,726 ULB + 640 explicitly
  synthetic). Full-data overview aggregation measured .174 seconds in one local
  request; this is not a throughput or memory guarantee.
- Browser verification on actual ULB data passed: overview, source/flag filters,
  XGBoost SHAP, Laboratory, mobile layout; no page errors. Actual screenshots
  reviewed; plot animations disabled to prevent incomplete captures.
- GitHub Actions baseline `d08d46e`: **all four jobs passed**, including complete
  Docker Compose build/start, PostgreSQL health, 600 demo rows scored through the
  frontend API proxy, backend tests, browser flows, frontend checks/audit.
  Evidence: https://github.com/muratkareem/argus/actions/runs/40332175925
- Full-ULB/SQL milestone `dcfa217`: all four CI jobs passed again.
  Evidence: https://github.com/muratkareem/argus/actions/runs/40333965624
- Repeated full-data runs reproduced every candidate’s evaluation metrics exactly.
  PR plot sampling now preserves recall transitions and endpoints, with a new
  regression test. Final code revision `e2ad48c` passed all four CI jobs.
  Evidence: https://github.com/muratkareem/argus/actions/runs/40334710892
- Frontend bundle retains upstream notices in public/THIRD_PARTY_NOTICES.txt.

## Git and continuation

Account verified as muratkareem. Repository was absent and created public.
No existing remote work overwritten. Commits `971d2fc` (backend/ML) and
`d08d46e` (analyst workspace/Compose/CI), and `dcfa217` (full ULB benchmark) were pushed. Credential-pattern checks
passed before commits. Read-only ChatGPT project `sources/` untouched.

Local ignored `.env` selects the task-owned PostgreSQL cluster at loopback 55432.
Its files are `.local/postgres`; ULB and synthetic model versions are in
`ml/artifacts`. Stratified ULB XGBoost is active; the chronological run is retained
for comparison. Preview/API/database processes are stopped after verification;
all local data and artifacts are preserved. To resume this exact local workspace:

```sh
/opt/homebrew/opt/postgresql@17/bin/pg_ctl -D .local/postgres -l .local/postgres.log -o "-p 55432 -h 127.0.0.1 -k /private/tmp" start
PYTHONPATH=backend uv run uvicorn app.main:app --host 127.0.0.1 --port 8000
# In another terminal: cd frontend && npm run dev
```

`bootstrap.py` refuses to overwrite a non-synthetic active model;
use separate database/artifact paths to set up a new synthetic test workspace.
Default fresh-clone/Compose setup is synthetic, needs no private data, and trains
its own model. For ordinary setup use README commands.

## Explicit remaining limitations

- Installed Ollama/model integration is unverified; enabled path uses a mock.
- PDF reports and graph entity case links are planned, clearly labeled in UI/docs.
- No authentication, authorization, schema migrations, bank connectivity,
  compliance claim, calibrated probabilities or production assurance.
- Imports/scoring are synchronous and memory-bound; no large-scale load testing.
- Experiments are single-seed estimates without confidence intervals or external
  validation. Dashboard metrics over imported training data are not held-out
  research metrics; Laboratory reports are the benchmark evidence.
