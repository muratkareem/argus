# ARGUS

**AI-Powered Credit Card Fraud Detection & Investigation Platform**

A local, open-source analyst workspace for reproducible fraud research: import
transactions, run real ML inference, inspect SHAP contributions, compare held-out
metrics, and document investigations in a persistent database.

[![ARGUS verification](https://github.com/muratkareem/argus/actions/workflows/ci.yml/badge.svg)](https://github.com/muratkareem/argus/actions/workflows/ci.yml)

> Educational research prototype. Synthetic demonstrations are labeled throughout.
> Model scores are uncalibrated. No banking-grade security, compliance, or
> production fraud-prevention claim is made.

![Actual ARGUS workspace with synthetic records](docs/screenshots/overview.png)

## What works

- **ML core:** Logistic Regression, Random Forest, XGBoost; seeded splits,
  train-only preprocessing, class weighting, small validation parameter search,
  validation-selected thresholds/algorithm, untouched test evaluation, serialization.
- **Research:** precision, recall, F1, average precision, ROC-AUC, false-positive
  rate, confusion matrices, PR curves, feature importance and saved experiment JSON.
- **Data:** validated ULB-shaped CSV imports, duplicates, provenance, batch inference,
  search/filter/sort/pagination, transaction details, CSV/JSON exports.
- **Analyst workspace:** dark React dashboard driven by stored records, source
  badges, transaction drill-down and actual per-record SHAP explanations.
- **Investigations:** database-backed cases, linked transactions, priorities,
  five statuses, notes, analyst decisions, search and dated JSON reports.
- **Graph:** Cytoscape zoom/pan, entity selection and type highlighting over a
  separate synthetic relational fixture stored in SQL.
- **Optional Copilot:** selected records passed to local Ollama through a read-only
  evidence boundary. Gracefully disabled by default; the main app is independent.
- **Engineering:** PostgreSQL, Docker Compose, CI, backend/integration/ML tests,
  frontend component tests, Chromium browser workflows, responsive screenshots.

Every navigation item has an implemented page. Graph entity case-linking and PDF
reports are explicitly planned; the transaction investigation workflow works now.

## Quick start with Docker

Requires Git and Docker with Compose. From a terminal:

```sh
git clone https://github.com/muratkareem/argus.git
cd argus
cp .env.example .env
```

Set a private `POSTGRES_PASSWORD` in `.env` (a hex password avoids URL escaping
issues), then run:

```sh
docker compose up --build --wait --wait-timeout 240
```

- Workspace: [localhost:8080](http://localhost:8080)
- API schema: [localhost:8000/docs](http://localhost:8000/docs)
- Health: [localhost:8000/api/v1/health](http://localhost:8000/api/v1/health)

First startup explicitly seeds a **synthetic** 2,000-row training experiment,
600 independent demo transactions, and a separate relationship graph. Set
`ARGUS_SEED_DEMO=false` in `.env` for an empty research workspace. PostgreSQL and
model files persist in named volumes. `docker compose down` stops services and
preserves those volumes. Ports bind only to loopback.

For a ULB model in Compose, place an authorized CSV under `data/private/` and run
an offline training container with a read-only input mount:

```sh
docker compose run --rm \
  -v "$PWD/data/private:/input:ro" backend \
  python -m app.ml --csv /input/creditcard.csv
```

Then import it with **ULB benchmark data** provenance. Existing synthetic
predictions remain versioned; the active ULB model will not rescore them.

## Native development

Requires Python 3.12, [uv](https://docs.astral.sh/uv/), and Node.js 24+. Run from
the repository root:

```sh
uv sync --frozen
PYTHONPATH=backend uv run python scripts/bootstrap.py
PYTHONPATH=backend uv run uvicorn app.main:app --host 127.0.0.1 --port 8000
```

In another terminal:

```sh
cd frontend
npm ci
npm run dev
```

Open [localhost:5173](http://localhost:5173). Without database configuration this
native shortcut uses SQLite (`argus.db`) as an explicit local fallback. To use
PostgreSQL, create an empty research database and set its connection in `.env`
before bootstrap/server startup:

```dotenv
ARGUS_DATABASE_URL=postgresql+psycopg://argus:YOUR_PASSWORD@127.0.0.1:5432/argus
```

`.env`, databases, private datasets, credentials, model binaries and local caches
are ignored. The API creates its initial tables; schema migrations are a roadmap
item. Run native commands from the root so artifact/database paths agree.

## Training and authorized data

The intended benchmark is the [ULB / Worldline dataset on Kaggle](https://www.kaggle.com/datasets/mlg-ulb/creditcardfraud):
284,807 transactions and 492 fraud cases, with Time, Amount, V1–V28 and Class.
The repository does not contain this dataset or claim results on it. Download
through the source's authorized route after reviewing its terms. See
[dataset import instructions](docs/DATASETS.md).

```sh
# Reproducible artificial-data experiment
PYTHONPATH=backend uv run python -m app.ml --synthetic

# Authorized local ULB copy; new version becomes active after successful training
PYTHONPATH=backend uv run python -m app.ml --csv data/private/creditcard.csv

# Separate time-based sensitivity experiment
PYTHONPATH=backend uv run python -m app.ml \
  --csv data/private/creditcard.csv --split chronological
```

The default split is stratified 60/20/20. Identical feature rows are deduplicated
before splitting; conflicting duplicate labels are rejected during training.
Preprocessing fits only training data. Each algorithm has two parameter candidates,
selected by validation AP. Validation F1 chooses its threshold; validation AP
chooses the algorithm before test evaluation. The Laboratory reads saved reports.

### Actual synthetic research run

The following was measured on the seeded **artificial fixture**, not ULB, and
is useful only for checking the pipeline. Synthetic prevalence is ~6% and feature
shifts deliberately make the problem learnable. These results do not establish
real-world detection performance.

| Algorithm | Test precision | Test recall | Test F1 | Test AP | Test ROC-AUC |
|---|---:|---:|---:|---:|---:|
| Logistic Regression | 1.0000 | 0.9167 | 0.9565 | 1.0000 | 1.0000 |
| Random Forest | 0.9600 | 1.0000 | 0.9796 | 1.0000 | 1.0000 |
| XGBoost | 0.9600 | 1.0000 | 0.9796 | 0.9983 | 0.9999 |

[Full measured run, parameters, provenance, partitions and environment](docs/research/synthetic-evaluation.json).
The active algorithm was Logistic Regression, selected by **validation** AP.
The dashboard's labeled-record detection rate is separate from held-out test recall.

Severe imbalance makes accuracy misleading: an all-legitimate classifier can
achieve high accuracy while missing every fraud. Read the
[ML methodology and limitations](docs/ML_METHODOLOGY.md) before interpreting scores.
V1–V28 are anonymized; explanations never infer a merchant, location or behavior.

## Architecture and stack

```mermaid
flowchart LR
    Browser[React analyst workspace] --> API[FastAPI modular monolith]
    API --> SQL[(PostgreSQL)]
    CSV[ULB CSV / labeled synthetic fixture] --> API
    Training[Offline sklearn + XGBoost training] --> Artifacts[Versioned model + evaluation JSON]
    Artifacts --> API
    API --> SHAP[SHAP contributions]
    API -. selected read-only evidence .-> Ollama[Optional local Copilot]
```

React, TypeScript, Vite, Tailwind CSS, Lucide, Recharts, Cytoscape.js;
FastAPI, Pydantic, SQLAlchemy, psycopg; pandas, NumPy, scikit-learn,
XGBoost, SHAP, joblib; PostgreSQL 17; pytest, Vitest, Playwright, Ruff, ESLint.
No distributed infrastructure or external LLM service is required.

See [architecture](docs/ARCHITECTURE.md) and [API reference](docs/API.md).

## Optional local Ollama

Install and start Ollama separately, then:

```sh
ollama pull llama3.2
```

Set `ARGUS_OLLAMA_ENABLED=true` and optionally `ARGUS_OLLAMA_MODEL` in `.env`,
then restart the native backend or recreate the Compose backend. Native default
URL is `http://127.0.0.1:11434`; Docker uses `host.docker.internal`. Linux Docker
may need a host-gateway configuration. Supply an existing transaction/case ID
in the Copilot page. No SQL or shell execution tool is exposed.

Enabled/disabled API behavior is tested, with the enabled Ollama response mocked.
An installed local model has not been integration-tested in this environment.
LLM output can contain errors despite grounding instructions; verify every claim.

## Verification

```sh
uv run ruff check backend scripts
uv run ruff format --check backend scripts
uv run python -m compileall -q backend scripts
uv run pytest -q

# Optional PostgreSQL suite: creates and removes isolated test schemas only
ARGUS_TEST_DATABASE_URL=postgresql+psycopg://USER:PASSWORD@localhost/argus_test \
  uv run pytest -q

cd frontend
npm ci
npm run lint
npm test
npm run build
npx playwright install chromium
npm run test:e2e
```

Browser tests require a bootstrapped synthetic workspace. They start/reuse local
servers and import additional artificial rows and a case; use a development
database. CI uses disposable databases and needs no private dataset or credentials.
GitHub Actions also builds and starts the complete Compose stack and checks real
PostgreSQL connectivity, synthetic ML inference, and the frontend proxy.

See [implementation status and verification evidence](docs/IMPLEMENTATION_STATUS.md)
for current pass/fail results and platform-specific limits.

## Limitations and roadmap

Local educational use only: no user authentication, production authorization,
migrations, regulatory certification, guaranteed calibration or full-dataset
performance claim. Uploads/scoring and dashboard aggregation are memory-bound.
A single active model is supported; incompatible provenance is rejected. Models
are trusted server-owned joblib files; never place untrusted binaries in that
folder. CORS is restricted, queries are parameterized, uploads are validated and
bounded, and model/data directories are excluded from publication.

The graph is a **separate synthetic relationship fixture**, not inferred ULB
relationships. No ULB benchmark or installed-Ollama result has been fabricated.
PDF export and graph entity case links are planned. See the [roadmap](docs/ROADMAP.md).

## License and acknowledgements

Original ARGUS code: [MIT](LICENSE). Third-party library and dataset licenses
remain their own. The four requested reference projects were reviewed without
copying their source, model files, UI assets or data. Review findings and dependency
attribution are in [OPEN_SOURCE_ATTRIBUTION.md](docs/OPEN_SOURCE_ATTRIBUTION.md).

ARGUS is an original design inspired by dense enterprise analysis workflows;
it contains no proprietary Palantir branding, assets or code.
