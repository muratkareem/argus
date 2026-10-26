# ARGUS implementation status

Updated: 26 October 2026. The existing MVP and enterprise analyst upgrade are
implemented and published at https://github.com/muratkareem/argus.

## Enterprise upgrade delivered

- Flat compact original ARGUS design system; density preferences; shared UI
  primitives; separate transaction, investigation, graph and Copilot page modules.
- Command Center with stored-data analytics, active model metrics, recent cases,
  interactive chart/risk ranges linked to validated transaction queries.
- Advanced transaction query builder: amount/time/score/label/provenance filters,
  persisted shared local saved views, sorting/pagination and export/query parity.
  Invalid queries hide stale results and recover after correction.
- Global actual-record search with Cmd/Ctrl+K, record deep links, Escape and
  contained dialog focus. No invented object types are attached to ULB records.
- Resizable three-pane investigation workbench: queue, audit timeline/decisions,
  contextual transaction/SHAP/synthetic-entity evidence. Pointer/keyboard widths
  persist locally. Stale responses and overlapping saves cannot reset edits.
- Additive SQL `saved_views`, `case_events`, `case_entities` tables. Existing case
  creation/note timestamps are retained; unrecorded past transitions are not invented.
- Synthetic graph neighborhood expansion (0–4 hops), entity/relationship filters,
  shared-device structural cue, accessible node selection, neighbor traversal and
  bidirectional case/entity links. No inferred ULB account/device/card relationships.
- Bounded read-only Copilot context, stored scores, compatible versioned SHAP,
  source records and structured citation-ID validation. Unknown structured IDs
  are rejected. UI supports explicit labeled LLM-note saving as an analyst action.
- Real installed qwen2.5:7b API and browser integration verified using synthetic
  records. Valid citations do not guarantee every generated factual claim.
- Actual desktop/mobile screenshots, updated architecture/API/dataset/roadmap
  documentation and public design research references. No proprietary assets copied.

## Academic core and preservation

Original ML training implementation, ULB source CSV, model artifacts, PostgreSQL
records and stratified/chronological evaluation reports are preserved. No full
ULB retraining or reimport was performed as part of this upgrade. Browser regression
work used a separate synthetic database/model directory under `.local/upgrade-e2e*`.

Before/after activation and read-only QA on the original full-data workspace:
284,366 transaction fingerprints/scores/thresholds/model versions, 3 datasets,
1 case, 1 note, 31 synthetic entities and 36 relationships matched. CSV SHA-256,
active model binary/version and both evaluation JSON checksums matched exactly.
Evidence: `docs/research/upgrade-preservation.json`.

- Authorized original CSV: 284,807 rows; 1,081 duplicates removed; 283,726 unique
  ULB rows and 473 frauds. The original workspace also retains 640 synthetic rows.
- Stratified validation-selected XGBoost: test precision .9474, recall .7579,
  F1 .8421, AP .8069, ROC-AUC .9793 (56,746 test rows / 95 frauds).
- Chronological validation-selected Logistic Regression: test precision .9423,
  recall .6622, F1 .7778, AP .7475, ROC-AUC .9818 (56,746 rows / 74 frauds).
- Logistic Regression, Random Forest, XGBoost, train-only preprocessing,
  validation-only tuning/threshold selection, held-out evaluation, SHAP and
  provenance guards remain intact. Dashboard rates are not held-out metrics.

## Executed verification

| Check | Actual result |
|---|---|
| Backend / ML / API on SQLite | 23 pytest tests passed |
| Backend on PostgreSQL 17 | Same 23 tests passed in isolated schemas |
| Python quality | Ruff lint/format and compile checks passed |
| Frontend components | 3 Vitest tests passed |
| Frontend quality/build | ESLint, TypeScript, Vite production build passed |
| Default browser workflows | All 11 Playwright flows passed |
| Real local-model API | qwen2.5:7b, supplied citation IDs only, DB counts unchanged |
| Real local-model browser | Context/source inspection, generation, explicit labeled-note save passed |
| Full original ULB workspace | Dashboard, filters/export parity, search, SHAP, Laboratory, graph and mobile QA passed |
| Preservation | Original transaction/model/dataset/report fingerprints matched |
| CI code revision 9bef4c4 | All 4 jobs passed, including actual Chrome workflows and Docker Compose |

CI evidence: https://github.com/muratkareem/argus/actions/runs/40353906621
The final documentation/screenshots commit receives the same automated checks.

Real-model evidence: `ollama-integration.json` and `ollama-ui-verification.json`
under `docs/research`. Full-data query observations and mobile checks are in
`full-workspace-upgrade-check.json`. These are single-host observations, not
throughput/concurrency guarantees. Current npm audit reported no vulnerabilities.

CI browser provisioning was improved after an external browser/dependency install
step stalled before tests began. Playwright now uses explicitly version-printed
image-provided Chrome on Ubuntu 24.04. All 11 tests still run; none are skipped.
Local tests continue using downloaded Chromium. Prior verified MVP CI also built
and started PostgreSQL + FastAPI + frontend with actual synthetic ML inference.

## Local continuation

The task-owned preview/API/PostgreSQL processes are stopped after verification;
data and artifacts are preserved. Existing Ollama was already running independently.
Ignored `.env` selects PostgreSQL on loopback port 55432. Original data remains
in `data/private`, active ULB artifacts in `ml/artifacts`, PostgreSQL cluster in
`.local/postgres`. To resume from this repository root:

```sh
/opt/homebrew/opt/postgresql@17/bin/pg_ctl -D .local/postgres -l .local/postgres.log -o "-p 55432 -h 127.0.0.1 -k /private/tmp" start
PYTHONPATH=backend uv run uvicorn app.main:app --host 127.0.0.1 --port 8000
# In another terminal: cd frontend && npm run dev
```

For the verified installed Copilot, add `ARGUS_OLLAMA_ENABLED=true` and
`ARGUS_OLLAMA_MODEL=qwen2.5:7b` to the API process environment. Ordinary fresh-clone
and Compose setup remain synthetic and disabled-by-default without private data.
`bootstrap.py` refuses to replace a non-synthetic active model. All project
`sources/` reference files remain untouched. No credentials, private datasets,
local database or model binary is committed; staged secret-pattern scans passed.

## Remaining limitations

- Research prototype: no authentication, authorization or multi-user isolation.
  Saved views are shared in the local workspace. Existing-schema migrations,
  immutable administrative audit storage and PDF reports remain future work.
- Graph relationships are synthetic. Case links are analyst associations and do
  not establish relationships between graph fixtures and ULB records.
- Scores are uncalibrated. Single-seed benchmark estimates lack confidence
  intervals/external deployment validation; full-data dashboard metrics include
  training rows and are separate from held-out Laboratory reports.
- LLM interpretations need analyst verification. Valid source IDs do not prove
  factual correctness; other model families/configurations are unverified.
  Context is deliberately bounded and truncation is disclosed.
- Imports/scoring remain synchronous. No production load/security/compliance
  claim. Browser coverage is Chromium/Chrome with tested responsive viewports,
  not an exhaustive assistive-technology/device certification.
