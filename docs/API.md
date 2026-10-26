# API quick reference

Interactive schema: `http://127.0.0.1:8000/docs`; OpenAPI JSON: `/openapi.json`.
All business paths below begin with `/api/v1`. No authentication is implemented;
use only locally or in a trusted private research environment.

| Method | Path | Purpose |
|---|---|---|
| GET | `/health` | Database connectivity and backend status |
| GET | `/settings` | Nonsecret runtime settings |
| GET | `/datasets` | Imported dataset provenance and counts |
| POST | `/datasets/upload` | Multipart `file` + `provenance=ulb\|synthetic`; 192 MiB limit |
| POST | `/datasets/{id}/score` | Explicitly rescore a dataset with matching active model |
| GET | `/transactions` | `q`, `flagged`, `provenance`, `min_risk`, `sort`, `direction`, `page`, `page_size` |
| GET | `/transactions/export` | Matching `q`, `flagged`, `provenance`, `min_risk`; `format=csv\|json` |
| GET | `/transactions/{id}` | Stored score, version, all features, linked cases |
| GET | `/transactions/{id}/explanation` | Actual active-model SHAP values and stored-version match flag |
| POST | `/predict` | Validated feature object and explicit provenance |
| GET | `/overview` | Statistics from stored records |
| GET | `/models` | Active version and saved experiment reports |
| GET, POST | `/cases` | Search (`q`) or create with `title`, `priority`, `transaction_ids` |
| GET, PATCH | `/cases/{id}` | Retrieve or save status/priority/decision |
| POST | `/cases/{id}/transactions` | Link `{transaction_id}`; idempotent |
| POST | `/cases/{id}/notes` | Append `{body}` analyst note |
| GET | `/cases/{id}/export` | Dated JSON report, scores, model versions, provenance, disclaimer |
| GET | `/graph` | Separate synthetic entity/edge records; optional `kind` |
| POST | `/copilot` | `{question, transaction_id?, case_id?}` with selected read-only evidence |

Prediction request:

```json
{"provenance":"synthetic","features":{"Time":0,"V1":0,"V2":0,"V3":0,"V4":0,"V5":0,"V6":0,"V7":0,"V8":0,"V9":0,"V10":0,"V11":0,"V12":0,"V13":0,"V14":0,"V15":0,"V16":0,"V17":0,"V18":0,"V19":0,"V20":0,"V21":0,"V22":0,"V23":0,"V24":0,"V25":0,"V26":0,"V27":0,"V28":0,"Amount":42}}
```

The response includes `model_version`, `risk_score`, `classification`,
`decision_threshold`, `provenance`, and processing `metadata`. Classification is
`flagged` or `clear`, not a definitive fraud determination. Untrained models
return 503; incompatible provenance returns 409; validation returns 422.

Case statuses: Open, In Review, Escalated, Resolved, False Positive.
Priorities: Low, Medium, High, Critical.

Transaction CSV includes source, model version, threshold, and optional observed
label. JSON exports add export time and a research disclaimer. Model experiment
JSON is downloadable from the Laboratory and contains measured evaluation time,
dataset fingerprint, environment, provenance, partitions, and model metrics.
PDF export is planned, not presented as implemented.
