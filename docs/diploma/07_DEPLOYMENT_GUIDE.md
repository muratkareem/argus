# Deployment guide

## Native CPU workflow

Requires Python 3.12, uv and Node 24+. From repository root:

```sh
uv sync --frozen
PYTHONPATH=backend uv run python scripts/bootstrap.py
PYTHONPATH=backend uv run uvicorn app.main:app --host 127.0.0.1 --port 8000
```

In a second terminal: `cd frontend && npm ci && npm run dev`. Open http://127.0.0.1:5173. Native defaults use SQLite argus.db and ml/artifacts. Bootstrap trains only when no active synthetic model exists; repeated calls reuse the model and existing 600 independent demonstration rows. It refuses an incompatible active ULB model instead of overwriting it. API startup/bootstrap run additive migrations; back up databases before upgrades. Use one migration/startup process before adding workers.

## Docker Compose

```sh
cp .env.example .env
# Set a private hexadecimal POSTGRES_PASSWORD in .env.
docker compose up --build --wait --wait-timeout 240
```

Open http://127.0.0.1:8080; API docs http://127.0.0.1:8000/docs. Named volumes preserve PostgreSQL and model artifacts; `docker compose down` stops containers while retaining data. Do not use down -v on valuable workspaces. ARGUS_SEED_DEMO=false starts empty. Loopback-only port bindings are deliberate. No GPU or generative service is needed. Set ARGUS_API_KEY for optional shared Bearer access; enter it in System Information in the browser. Native CORS permits localhost/127.0.0.1:5173; configure exact origins for other deployments.

## Dataset and model reproduction

Authorized CSV belongs in ignored data/private. Do not redownload an existing copy. To train a NEW experiment when needed (not required to resume completed runs): `PYTHONPATH=backend uv run python -m app.ml --csv data/private/creditcard.csv --out ml/artifacts`; add `--split chronological` for temporal evaluation. The completed local artifacts are at .local/ulb-stratified and .local/ulb-chronological; set ARGUS_ARTIFACT_DIR to one before API startup to reuse them. Import ULB CSV with ulb provenance. Synthetic data cannot use a ULB model and vice versa. current.json controls activation; preserve whole version directory and checksum manifest.

## Troubleshooting

503 prediction/readiness: no valid trusted model; check artifact path and manifest.409: incompatible provenance or model changed during a batch; retry with matching model.422: invalid schema, negative amount/time, missing/nonfinite features or invalid filters.401: configure the same key in API environment and browser session. CSV limit 192MiB, batch limit 1000. Keep commands rooted at repository to align relative database/model paths. Docker permission/socket failure requires a running Docker engine and authorized socket access. Inspect local API/Compose logs; validation responses omit raw inputs and SQL errors omit database details.
