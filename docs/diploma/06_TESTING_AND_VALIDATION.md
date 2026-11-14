# Testing and validation

Backend tests cover exact schemas/nonfinite input, missing model, provenance isolation, single/batch consistency, request thresholds, risk outputs, SHAP for every candidate, additivity/cache, artifact integrity, repeated training, concurrent activation, duplicate labels, transactional rollback/concurrent imports, migration preservation, SQLite foreign keys, query plans, bounded graph neighborhoods, saved views, investigation persistence and optional authentication/CORS.

Latest recovery: `.venv/bin/pytest -q`77 passed in5.41s; Ruff lint and formatting passed. Previous checkpoint also verified77 tests against an isolated PostgreSQL17 cluster in8.77s. One Starlette/httpx TestClient deprecation warning remains. No coverage percentage was measured.

Frontend: `npm run lint`, `npm test`12 tests across5 files, `npm run build` previously pass; final run evidence is tracked in PROGRESS.md. Playwright includes navigation, import/explorer/filter/search, investigations, graph and direct feature prediction→risk→SHAP plus validation threshold profiles. Earlier run11/12 passed; corrected assertion passed targeted rerun. Consult PROGRESS.md for final clean full-suite result; do not equate separate runs with a clean full run.

Commands from root: `.venv/bin/ruff check backend scripts`, `.venv/bin/ruff format --check backend scripts`, `.venv/bin/python -m compileall -q backend scripts`, `.venv/bin/pytest -q`. Optional PostgreSQL suite uses `ARGUS_TEST_DATABASE_URL` and creates isolated test schemas. From frontend: `npm run lint && npm test && npm run build`, then `ARGUS_BROWSER_CHANNEL=chrome npm run test:e2e` against an isolated bootstrapped development DB/model. Browser tests write synthetic records and screenshots; never aim them at a valuable workspace.

Nine moderate development dependency advisories were observed; no high/critical advisories were reported. Audit results are point-in-time and do not establish vulnerability freedom. Docker and final browser verification status appear in PROGRESS.md.
