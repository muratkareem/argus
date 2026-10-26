# Open-source review and attribution

Reviewed 26 October 2026 using GitHub repository metadata, recursive trees,
README files, available LICENSE files, notebooks, and selected Python sources.
No source, model, dataset, notebook, layout, or image was copied or adapted from
these candidates. ARGUS application code is independently implemented under MIT.
No binary or pickle from a reference repository was loaded.

| Candidate | License observed | Architecture and ML review | Decision / verification limits |
|---|---|---|---|
| [tcharkow/fraud-detection](https://github.com/tcharkow/fraud-detection) | No LICENSE in recursive tree; GitHub license null | Notebook with ULB-shaped analysis, three classifiers, training-only SMOTE described in README; JSON dashboard exports. 14 files, 2 commits shown; pushed 2026-06-21. Repository contents were narrower than the repository description's API/dashboard claim. | No reuse: no explicit license. Training/inference were not executed; no dataset available during candidate review. Static exports do not provide ARGUS persistence/workflows. |
| [FelipeToroG/ml-fraud-detection-pipeline](https://github.com/FelipeToroG/ml-fraud-detection-pipeline) | MIT; LICENSE read | Modular loader/features/API, notebooks, cost-sensitive analysis, SHAP, API tests, serialized XGBoost artifact. Read prediction service and test_api source. Correctly emphasizes serializing preprocessing with classifier; includes native XGBoost contribution path for a stated SHAP compatibility issue. 49 files; pushed 2026-06-11. | Suitable conceptual reference; no code/model reuse. Existing config and cost assumptions would need separate validation. No database-backed investigation workspace. Candidate tests/inference not executed; model artifact is untrusted and dataset unavailable during candidate review. |
| [tharinm/FraudShield-AI](https://github.com/tharinm/FraudShield-AI) | No LICENSE in recursive tree; GitHub license null | FastAPI, Next.js, separate preprocessing/training notebooks, committed model/scaler files, quick-training and mock-model scripts. 63 files, 18 commits shown; pushed 2026-07-12. Presence of mock code is a reason to verify serving paths, not evidence that all predictions are mocked. | No reuse: no explicit license. Candidate training/inference not executed. Avoid inheriting disconnected preprocessing and mock fallback ambiguity. |
| [oualidall/fraud-detection-mlops](https://github.com/oualidall/fraud-detection-mlops) | MIT; LICENSE read | Read training source, API tests, README and tree. CLI, XGBoost/baseline factories, MLflow runs, validation metrics, model bundle with feature/category mapping, monitoring and Grafana. 36 files, 8 commits shown; pushed 2026-09-28. | No reuse: operational stack heavier than this MVP. Viewed training entry point reports validation metrics; that alone does not establish an untouched final test benchmark. Candidate pipeline was not executed; dataset/services unavailable during candidate review. |

Existence, code review, and license observations are verified. Candidate runtime
correctness and maintenance quality beyond this snapshot are **not** certified.
Repository activity is descriptive, not a guarantee of correctness.

## Libraries used

Dependencies are installed from their own distributions, with upstream notices
retained in those distributions. See `uv.lock` and `frontend/package-lock.json`
for exact resolved versions and npm package license metadata.

- FastAPI, Pydantic, SQLAlchemy, Uvicorn: MIT/BSD-family licenses.
- NumPy, pandas, scikit-learn, SciPy: BSD-family licenses.
- XGBoost: Apache-2.0; SHAP and joblib: MIT/BSD-family licenses.
- psycopg: LGPL-3.0-or-later; dynamically imported as a separate dependency.
- React, Vite, Tailwind CSS, Recharts, Cytoscape.js: MIT.
- Lucide icons: ISC. ARGUS uses library icons with their package notices.
- pytest, Ruff, Vitest: MIT; Playwright: Apache-2.0.

ARGUS's MIT license covers original repository code, not third-party packages,
ULB data, or models trained from third-party data. Distributing bundled packages
must preserve their respective license and notice files. No proprietary
Palantir assets or layouts are used.

The built frontend ships `THIRD_PARTY_NOTICES.txt` from `frontend/public/`,
including upstream production dependency notices and the nested D3/internmap
notices in victory-vendor. Vite copies this file into the deployed static assets.
Refresh these notices when changing frontend dependencies.
