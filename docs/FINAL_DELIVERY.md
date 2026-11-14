# Final main-branch delivery

## Verified scope

Existing 42-commit development history is preserved. Delivery adds compatible dependency fixes, official dataset license/attribution review, calibration assessment, real-data integration/performance evidence and a strict floating-point reproducibility test correction. No full ULB experiment or dataset download was repeated. Official English, Russian and Kazakh thesis titles are in diploma/01_PROJECT_OVERVIEW.md.

Local gates on14 November2026: SQLite78/78 after correcting a machine-precision metric assertion; PostgreSQL78/78; frontend12/12; Chrome browser12/12; lint/typecheck/format/build/compile checks pass. Docker Compose built, all services became healthy, frontend proxy/600 scores/readiness/PostgreSQL smoke passed. The only tracked CSV is the explicitly synthetic sample; raw ULB, SQL state, trained binaries and private environment files stay ignored. Full tracked-tree and staged credential-pattern scans passed.

A separate browser check loaded993 real ULB rows (first1000 source rows deduplicated), browsed stored evidence, generated stored/direct SHAP and predicted using the existing XGBoost model with no page errors. First navigation to dashboard snapshot measured153.26ms in one headless Chrome/Vite/local-SQLite run, not a cold OS or p95 claim. A focused in-process real-data check measured fresh artifact load2.31ms, first SHAP150.84ms, repeated SHAP7.57ms, prediction p95 at concurrency4 over40 requests23.75ms, and one1000-row batch27.18ms. Full output/methodology: research/delivery-real-{data-check,browser}.json and scripts/verify_delivery.py. Earlier warm synthetic p95 prediction5.96ms/batch38.07ms and import allocation benchmarks remain historical evidence under their documented conditions.

## Research and security conclusions

Stratified validation selects XGBoost: test precision0.9474, recall0.7579,F1 0.8421, AP0.8069, ROC-AUC0.9793. Chronological validation selects Logistic Regression: precision0.9423, recall0.6622,F1 0.7778, AP0.7475, ROC-AUC0.9818. Test FP/FN are4/23 and3/25 respectively. Calibration curves/Brier scores are reviewed in diploma/CALIBRATION_REVIEW.md; Logistic Regression's Brier score around0.024 demonstrates why high discrimination and high thresholds do not imply calibrated risk. No test-based recalibration or reselection was performed. Multi-seed/external/drift/calibration validation remains future work.

Official Kaggle metadata confirms ODbL database/DbCL contents licensing. Attribution and relevant public-output/derivative conditions are documented in DATASET_LICENSE.md. Dataset rights remain separate from the MIT code license; no raw dataset is redistributed.

Compatible npm fixes reduce nine moderate development advisories to seven, all through typescript-eslint/minimatch. Production-only audit:zero; high/critical:zero. No breaking forced downgrade/override. SECURITY_REVIEW.md lists affected packages and remaining risk. Starlette/httpx test-client deprecation remains. No production/banking compliance claim is made.

## Delivery and reproduction

Use the native and Docker commands in diploma/07_DEPLOYMENT_GUIDE.md and the5–7minute defense scenario in diploma/08_DIPLOMA_DEMONSTRATION.md. Git delivery uses fetch, a fast-forward merge into main and a normal push; no history rewrite/squash/force. Remote main SHA and Actions status are verified after push and reported to the user. Live status: https://github.com/muratkareem/argus/actions . For full preserved history use `git log c7a4691..main`; remote checks may have different timings/platforms from local tests.
