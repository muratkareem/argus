# Requirements traceability

COMPLETE means implemented with cited execution evidence; PARTIAL means an implementation or verification limitation remains. This is a diploma research prototype, not a production certification. PROGRESS.md records final commands and deployment outcomes.

|Requirement|Component/source|Verification|Status|
|---|---|---|---|
|Remove generative runtime|main/config/frontend; removed assistant module|removed routes404, build and source scan|COMPLETE|
|Dataset suitability/audit|data.py, ml.py, source JSON|official CSV checksum and full-run audits|COMPLETE|
|Train-only preprocessing/dedupe/splits|ml.py|ML reproducibility/schema tests; two full experiments|COMPLETE|
|LR/RF/XGBoost comparison|ml.py|saved full ULB reports|COMPLETE|
|Threshold selection and tradeoffs|ml.py, PredictionForm, ModelDiagnostics|validation profiles, threshold and browser tests|COMPLETE|
|Calibration assessment|ml.py|Brier and reliability curves|COMPLETE assessment; calibration guarantee excluded|
|Single/batch prediction|main.py|API consistency/limits/provenance tests|COMPLETE|
|Cached model and safe activation|ml.py|checksum/concurrency/load-once tests|COMPLETE for trusted local artifacts|
|Local SHAP actual model/output|ml.py|all three algorithms, additivity/cache tests|COMPLETE|
|Global importance|ml.py, Laboratory|model-native importance JSON/UI|COMPLETE model-native; global SHAP summary remains PARTIAL|
|Overview/explorer|main.py, App/TransactionIntelligence|API aggregates/filters/pagination and browser tests|COMPLETE; explicit observed-label counts tested|
|Investigations|intelligence.py, InvestigationWorkspace|persistence/timeline/case tests|COMPLETE|
|Defensible graph|data.py, intelligence.py, GraphIntelligence|separate synthetic fixture, bounds/truncation tests|COMPLETE synthetic demonstration only|
|DB integrity/migrations/indexes|db.py|legacy migration/FK/query plan; SQLite/PostgreSQL suites|COMPLETE|
|Performance targets|scripts/benchmark*.py|measured warm10k fixture/import reports|PARTIAL full-data/concurrent/browser timing|
|Security/reliability|config/main/data/db|auth/CORS/nonfinite/rollback/provenance tests|COMPLETE private-demo scope; advisories pending|
|Frontend/build/unit|frontend/src|lint/typecheck/build and 12 tests|COMPLETE|
|Clean full E2E|frontend/e2e|final status in PROGRESS.md|COMPLETE: 12/12 clean final run|
|Native setup|bootstrap/entrypoint|repeat bootstrap reuses 600 records|COMPLETE native SQLite|
|Docker Compose|Dockerfiles,compose|final status in PROGRESS.md|COMPLETE: final three-service build/start/smoke|
|English diploma documentation|docs/diploma 01–10|artifact/link checks|COMPLETE documentation; research limits remain|

Dataset license text was not independently verified in this environment; source/rights review remains PARTIAL. The raw dataset is not redistributed. CI configuration is present, but remote GitHub checks were not triggered because no push was authorized.

License review completed: the official source specifies ODbL database / DbCL contents licensing. See [dataset attribution and conditions](../DATASET_LICENSE.md); research and demonstration use must preserve the applicable source/license notices. Raw data is not redistributed. This supersedes the earlier pending-license checkpoint.
