#!/bin/sh
set -eu
if [ "${ARGUS_SEED_DEMO:-false}" = "true" ] && [ ! -f "${ARGUS_ARTIFACT_DIR:-ml/artifacts}/current.json" ]; then
    python scripts/bootstrap.py
fi
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
