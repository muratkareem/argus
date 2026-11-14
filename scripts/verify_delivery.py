"""Focused real-data smoke and cold/warm checks using existing trusted ULB artifacts."""

import json
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from app.config import Settings
from app.main import create_app
from app.ml import FEATURES, Predictor
from fastapi.testclient import TestClient


def main():
    artifacts = Path(".local/ulb-stratified")
    frame = pd.read_csv("data/private/creditcard.csv", nrows=1000)
    predictor = Predictor(artifacts)
    started = time.perf_counter()
    bundle = predictor.load()
    load_ms = (time.perf_counter() - started) * 1000
    data = {"features": frame[FEATURES].iloc[0].to_dict(), "provenance": "ulb"}
    settings = Settings(
        database_url="sqlite:///./.local/real-verification.db", artifact_dir=artifacts
    )
    report = {
        "measured_at": datetime.now(timezone.utc).isoformat(),
        "source": "first 1000 rows of existing authorized ULB CSV; no retraining",
        "model": bundle["model_name"],
        "version": bundle["version"],
        "cold_artifact_load_ms": load_ms,
        "conditions": "In-process HTTP, local SQLite, existing XGBoost CPU artifact; cold load excludes interpreter imports and OS page cache is uncontrolled. Concurrency4,40 single requests; not production-scale evidence.",
    }
    with TestClient(create_app(settings)) as client:
        response = client.post(
            "/api/v1/datasets/upload",
            files={"file": ("ulb.csv", frame.to_csv(index=False).encode())},
            data={"provenance": "ulb"},
        )
        response.raise_for_status()
        report["imported"] = response.json()["imported"]
        rows = client.get("/api/v1/transactions?provenance=ulb").json()
        assert rows["total"] == len(frame.drop_duplicates(subset=FEATURES))
        report["stored_unique_rows"] = rows["total"]
        result = client.post("/api/v1/predict", json=data)
        result.raise_for_status()
        assert 0 <= result.json()["fraud_probability"] <= 1
        started = time.perf_counter()
        explanation = client.post("/api/v1/predict/explanation", json=data)
        explanation.raise_for_status()
        report["first_explanation_ms"] = (time.perf_counter() - started) * 1000
        assert explanation.json()["model_version"] == result.json()["model_version"]
        assert explanation.json()["additivity_error"] < 1e-4
        started = time.perf_counter()
        client.post("/api/v1/predict/explanation", json=data).raise_for_status()
        report["repeated_explanation_ms"] = (time.perf_counter() - started) * 1000

        def request(_):
            started = time.perf_counter()
            client.post("/api/v1/predict", json=data).raise_for_status()
            return (time.perf_counter() - started) * 1000

        with ThreadPoolExecutor(max_workers=4) as pool:
            timings = list(pool.map(request, range(40)))
        report["concurrent_prediction_p95_ms"] = float(np.percentile(timings, 95))
        batch = {
            "transactions": [{"features": r} for r in frame[FEATURES].to_dict("records")],
            "provenance": "ulb",
        }
        started = time.perf_counter()
        response = client.post("/api/v1/predict/batch", json=batch)
        response.raise_for_status()
        report["batch_1000_ms"] = (time.perf_counter() - started) * 1000
        assert response.json()["count"] == 1000
        assert client.get("/api/v1/models").json()["active_version"] == bundle["version"]
    Path("docs/research/delivery-real-data-check.json").write_text(
        json.dumps(report, indent=2) + "\n"
    )
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
