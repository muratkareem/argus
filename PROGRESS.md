# Full PaySim reliability study completed — 16 November 2026

Recovered the usage-limit interruption from the existing main checkout. All six full-data runs had completed, including chronological seed 2027; no source experiment was rerun during recovery. Last implementation/documentation commit before this checkpoint: `36b4b670706954e5ea9c83e5adaa05ac07906ca5`. Checkpoint hash: `git log -1 -- PROGRESS.md`. User explicitly authorizes normal pushes directly to main.

Completed evidence:
- Full official PaySim CSV reused without redownload: 6,362,620 records/8,213 frauds, zero duplicates. Stratified and chronological splits, seeds 42/2026/2027, all LR/RF/XGBoost grids fixed before execution. Six immutable report JSONs plus docs/research/paysim-full-summary.json were recovered/validated and committed. Actual training implementation is frozen at 46ac5a7; identical implementation checksums across all six reports were verified before subsequent caption/IEEE-clock corrections. No measurements were altered.
- Full stratified RF was selected by validation AP in 3/3 runs: test AP mean .206569, sample SD .010935; recall mean .181613, SD .015125. Chronological XGBoost selected 3/3: AP mean .221334, SD .005289; recall .182480 across all three. Every algorithm/seed, threshold, confusion matrix, error group and interval is retained, including unfavorable results.
- Primary seed 42 has 200-replicate conditional day-cluster intervals for precision/recall/F1/AP/ROC-AUC, with valid replicate counts and assumptions. Seed SD/range is descriptive sensitivity, not independent dataset replication or a naive population CI. Summary means/SD match raw report metrics exactly; independent statistics.mean/stdev checks pass.
- Low recall remains explicit. Primary stratified RF misses 1,360/1,642 frauds (all 829 TRANSFER frauds); lowering the threshold is analyzed only on validation. Chronological primary XGBoost misses 3,481/4,258 frauds. Source hours 719–743 contain 296 events, all fraud, so plots report both volume and prevalence. No feature/grid/threshold tuning followed test inspection.
- Chunked raw validation/fingerprints, cross-chunk duplicate conflicts, compact 206.3MiB retained inputs. Max process-lifetime RSS 2482.6875MiB on 16GiB/10-logical-CPU host. Six measured run durations total 1430.26s, including evaluation/diagnostics/bootstrap, excluding the shared initial read. Timings are not controlled throughput claims.
- Laboratory labels source scope/seed, defaults to the preregistered full chronological primary, displays conditional intervals, preserves active production artifacts. Full-study AP/SD and temporal/validation-threshold figures were regenerated solely from reports and visually inspected. README, dataset/methodology docs, reproduction/resume commands and source/license notices updated. Published reports remain unchanged; live Wilson captions now clarify their scope, and IEEE seconds are not mislabeled as PaySim hours.

Verification actually completed:
- 103 backend tests passed on SQLite (7.55s) and PostgreSQL (8.90s); Ruff check/format, compilation and scientific local-link checks pass. Existing Starlette/httpx deprecation warning remains.
- 18 frontend tests, ESLint/TypeScript, production build and 16 Chrome desktop/mobile workflows passed (25.4s). New browser assertions verify all 6 full reports, three seeds, primary selection and day-cluster intervals. Relevant CI Compose assertions require both split seed sets.
- Compose build/healthy frontend/API/PostgreSQL and proxied six-report smoke passed. Actual existing ULB prediction/SHAP smoke passed; both ULB activation manifests and `/models` remained unchanged. Original ULB and sampled PaySim reports are unchanged in Git.
- Credential-pattern scans and git whitespace checks passed. Browser-generated unrelated screenshots were preserved in ignored .local/reliability-browser-screenshots/ and tracked originals restored. Raw datasets, credentials, caches and model binaries remain ignored.
- Logs: .local/paysim-full-study.log, reliability-backend-final.log, reliability-postgres-final.log, reliability-browser.log, reliability-compose.log. No training process remains. GitHub Actions is checked for the final published commit after this checkpoint; consult its run at https://github.com/muratkareem/argus/actions/workflows/ci.yml.

Architecture / modified files:
Existing FastAPI/SQLAlchemy/React monolith retained. benchmark_data.py adds compact full loading; benchmark_reliability.py provides diagnostics, bootstrap, exclusive atomic checkpoints/resume and seed aggregation; benchmarks.py orchestrates offline reports. ml.partition_indices adds an optional seed with its original default unchanged. No new runtime dependency, production-model activation or DB migration. Full inventory: `git diff --name-status 2fa2210..HEAD`; tests in backend/tests/test_benchmark*.py and frontend Laboratory/e2e; plotting in scripts/plot_benchmarks.py. PROGRESS/NEXT_STEPS supersede historical incomplete-study notes below.

Remaining limits:
IEEE-CIS is still blocked by official HTTP 401; no new credentials, no retry during recovery, no substitute data or fabricated results. See docs/research/ieee-cis-access.json. PaySim is synthetic, single source, three seeds, conservative amount/log/type features; low recall, recurring entities, cross-day dependence and few/partial-day bootstrap clusters limit interpretation. No calibrated real-world probability, deployment guarantee or frozen-model cross-dataset transfer claim. Future studies require a new prospective design; do not rerun completed experiments merely to resume.

Historical checkpoints follow.

# Multi-dataset scientific extension — 15 November 2026

Baseline: 755ee20; working/publishing directly on main, explicitly authorized by the user. Last completed implementation/test commit before this checkpoint: `c31af03989a127419a025238c40f115b894f0d06`. Resolve this checkpoint's own hash with `git log -1 -- PROGRESS.md`. No ULB redownload/retraining, production artifact activation, database migration or cosmetic redesign was performed.

Completed:
- Explicit IEEE-CIS transaction/optional identity adapters and PaySim eleven-column adapter. One-to-one identity joins, schema/label/time validation, raw-event deduplication/conflict checks, deterministic uniform whole-source sampling.
- Independent report-only LR/RF/XGBoost training with seed 42, chronological/stratified 60/20/20, train-only median/scaling/one-hot preprocessing, validation-only candidate/threshold/algorithm selection, held-out metrics/curves, warm inference timings, conditional 95% Wilson precision/recall intervals.
- PaySim excludes all four balance fields per official source warning, policy flag and raw IDs. Amount, log amount and transaction type are the predictors; step only controls chronology.
- `/api/v1/benchmarks` validates and serves four actual reports plus dataset/access metadata. `/models`, ULB prediction/upload schemas, active artifacts, persisted investigations and SHAP contracts are unchanged. Docker bundles research reports.
- Laboratory dataset selector, verified comparison, honest IEEE access blocker, uncertainty and sampling/provenance displays; existing diagnostics reused. Scientific sources/licenses, reproduction commands, limitations and measured comparison figure added to existing docs.

Actual data/evidence:
- Existing authorized ULB CSV and both archived diploma reports reused unchanged (283,726 unique rows/473 frauds). No experiments repeated.
- Official author-linked PaySim download succeeded: 6,362,620 rows/8,213 frauds, 493,534,783 bytes, SHA256 16910f90577b0d981bf8ff289714510bb89bc71bff7d3f220f024e287e4eea6b. Private CSV: `data/private/paysim/paysim.csv`; not tracked.
- Seed 42 uniform 200,000-row sample/241 frauds. Stratified XGBoost selected by validation AP: test precision .4242, recall .2917, F1 .3457, AP .2707, ROC-AUC .9157. Chronological XGBoost: precision 1.0 (18 alerts), recall .1406 (18/128), F1 .2466, AP .2238, ROC-AUC .8917. Both reports retain all three algorithms, exact metrics, partitions and environment. No tuning followed test inspection.
- IEEE official competition API HTTP401. No Kaggle token, legacy environment credentials or credential file found. Authorized download/rule acceptance is still required; no real IEEE rows or metrics claimed. Fixtures verify training integration only.

Architecture/files:
- Existing FastAPI/SQLAlchemy/sklearn/XGBoost/React monolith retained. New `backend/app/benchmark_data.py` and `benchmarks.py`; additive endpoint/config in main/config; backend Docker report copy. No new runtime dependency.
- Tests: backend/tests/test_benchmark_data.py and test_benchmarks.py, frontend/src/pages/Laboratory.test.tsx, frontend/e2e/workspace.spec.ts; Laboratory.tsx/types.ts changed. CI smoke verifies bundled reports, allows future legitimate IEEE results.
- scripts/download_paysim.py and optional plot_benchmarks.py; docs/research/benchmarks contains measured reports and comparison.png; source/access evidence in docs/research. README, DATASETS, DATASET_LICENSE, ML_METHODOLOGY, API and diploma architecture updated. Complete inventory: `git diff --name-status 755ee20..HEAD`.

Verification actually run:
- 95 backend tests passed on SQLite (7.98s) and PostgreSQL (8.80s). Focused updated leakage/IEEE/report tests also pass. Existing Starlette/httpx deprecation warning remains.
- 18 frontend tests passed; ESLint, TypeScript and production build pass; Ruff check/format and Python compilation pass. Local links in modified scientific documentation resolve; staged credential-pattern scans pass.
- 16 Chrome desktop/mobile workflows passed (24.8s), including datasets, IEEE blocker, ULB/PaySim reports, threshold diagnostics, stored-data prediction/SHAP and investigations. Initial exact-label locator and incomplete typed-fixture failures were corrected. A pre-existing browser assertion failed once persisted counts reached 1,000; corrected locale formatting, then reran the entire suite successfully. Logs retained in ignored `.local/benchmark-*.log`.
- Compose build/health/proxied frontend/API/PostgreSQL smoke passed, including all four bundled reports and no report errors. Existing real ULB prediction/SHAP smoke passed; both ULB activation manifest hashes and `/models` contents remained unchanged.
- Browser-generated unrelated screenshot changes were preserved in `.local/regression-screenshots-final/` and the tracked originals restored. The scientifically relevant comparison figure is published separately. No raw datasets, credentials, binaries or caches are staged.
- Remote Actions are checked after publication of this checkpoint; consult the run for the final HEAD at https://github.com/muratkareem/argus/actions/workflows/ci.yml. Local gates above are measured, not a prediction of remote CI success.

Limitations/pending:
- IEEE authorized data unavailable; exact manual unblocking/reproduction commands are in docs/DATASETS.md. Published sizes/class counts remain unmeasured for IEEE.
- PaySim results cover a 200k sample, not full-source training. Only 17 chronological validation positives cause unstable thresholds; low held-out recall is reported honestly.
- Single seed, conservative feature baseline, conditional IID binomial intervals only. No AP/F1/AUC intervals, entity-group isolation, calibrated probabilities, deployment claim or cross-dataset model transfer claim.
- Keep current source/artifacts/reports intact. Next steps are prioritized in NEXT_STEPS.md; no further completed experiment needs repeating.

Historical checkpoints follow.

# UI/UX redesign completion — 15 November 2026

Recovered the interrupted UI work without restarting or discarding changes. Source commits on main: 55893ff route loading, e986725 navigation/progressive prediction/SHAP, 6f27f33 authenticated CSV export, 35ea3e4 explorer/evaluation/review simplification, e7a3b86 decorative-style cleanup/keyboard comparison access. Final local gates: 78 backend tests,16 frontend tests,15 clean Chrome workflows, lint/typecheck/format/build and isolated Compose/API docs smoke pass. No backend ML or dataset changes/retraining.33 current screenshots and39 preserved baseline images are indexed in docs/screenshots/README.md. Decision/performance evidence: docs/UI_REDESIGN.md and docs/research/ui-redesign-verification.json. Source and assets are authorized for direct main publication; exact published SHA/remote Actions result is verified after push. Temporary capture/audit helpers and interrupted generated images remain preserved in .local/. Historical checkpoint follows.

# Authorized main delivery — 14 November 2026

The user explicitly authorized normal publication to origin/main in the final-delivery attachment. The earlier no-push restriction is superseded for this delivery. Final review and exact local gates: docs/FINAL_DELIVERY.md. Source metadata/license review is complete; compatible npm updates reduce dev advisories from nine to seven, production-only audit zero. Real ULB browser/API/cold-warm/concurrency checks passed without retraining or redownload. The reproducibility assertion now tolerates1e-12 float roundoff while preserving exact count/structure checks. Main is delivered by fast-forward with all development commits preserved; remote SHA/Actions outcomes are checked after the push. See git log and the live Actions page for the immutable delivery commit/checks.

# ARGUS checkpoint — 14 November 2026

Branch: `development/diploma-ready`. All prior ML, Frontend and Data Security agent changes recovered; no overwrite or discarded work. No dataset redownload or repeated ULB training during recovery. Historical pre-delivery state: no changes had been pushed. Last implementation commit before final verification checkpoint: `03edbe9`; find this checkpoint's exact hash with `git log -1 -- PROGRESS.md`.

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
