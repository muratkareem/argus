"""Reproducible sequential, warm in-process HTTP benchmarks; no network/browser claims."""

import argparse
import json
import os
import platform
import resource
import statistics
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from app.config import Settings
from app.data import ingest
from app.main import create_app
from app.ml import FEATURES, Predictor, synthetic, train
from fastapi.testclient import TestClient


def measure(call, samples):
    for _ in range(3):
        response = call()
        if hasattr(response, "raise_for_status"):
            response.raise_for_status()
    values = []
    for _ in range(samples):
        started = time.perf_counter()
        response = call()
        if hasattr(response, "raise_for_status"):
            response.raise_for_status()
        values.append((time.perf_counter() - started) * 1000)
    return {
        "samples": samples,
        "p50_ms": statistics.median(values),
        "p95_ms": float(np.percentile(values, 95)),
        "min_ms": min(values),
        "max_ms": max(values),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--rows", type=int, default=10000)
    parser.add_argument("--samples", type=int, default=50)
    parser.add_argument("--artifacts", type=Path)
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix="argus-benchmark-") as directory:
        root = Path(directory)
        artifacts = args.artifacts or root / "models"
        if not (artifacts / "current.json").exists():
            train(synthetic(2000), artifacts, "synthetic")
        settings = Settings(database_url=f"sqlite:///{root}/benchmark.db", artifact_dir=artifacts)
        frame = synthetic(args.rows, seed=995)
        data = {"features": frame[FEATURES].iloc[0].to_dict(), "provenance": "synthetic"}
        predictor = Predictor(artifacts)
        with TestClient(create_app(settings)) as client:
            with client.app.state.session_factory() as session:
                imported = ingest(
                    session,
                    frame.to_csv(index=False).encode(),
                    "Synthetic benchmark seed 995",
                    "synthetic",
                    predictor,
                )
            results = {
                "health": measure(lambda: client.get("/api/v1/health"), args.samples),
                "prediction": measure(
                    lambda: client.post("/api/v1/predict", json=data), args.samples
                ),
                "transactions": measure(
                    lambda: client.get(
                        "/api/v1/transactions?page_size=20&flagged=true&sort=risk_score"
                    ),
                    args.samples,
                ),
                "overview": measure(lambda: client.get("/api/v1/overview"), args.samples),
                "shap_on_demand": measure(
                    lambda: client.get("/api/v1/transactions/1/explanation"), min(args.samples, 15)
                ),
                "vectorized_model_1000": measure(
                    lambda: predictor.predict(frame[FEATURES].iloc[:1000], "synthetic"),
                    min(args.samples, 20),
                ),
            }
            routes = client.get("/openapi.json").json()["paths"]
            if "/api/v1/predict/batch" in routes:
                batch = {
                    "transactions": [
                        {"id": str(i), "features": r}
                        for i, r in enumerate(frame[FEATURES].iloc[:1000].to_dict("records"))
                    ],
                    "provenance": "synthetic",
                }
                results["batch_api_1000"] = measure(
                    lambda: client.post("/api/v1/predict/batch", json=batch), min(args.samples, 20)
                )
            report = {
                "measured_at": datetime.now(timezone.utc).isoformat(),
                "methodology": "FastAPI TestClient in-process HTTP, concurrency 1, three warmups per operation; p95 interpolated; includes JSON and validation; excludes TCP, browser and TLS; synthetic seed 995.",
                "environment": {
                    "platform": platform.platform(),
                    "python": platform.python_version(),
                    "logical_cpu_count": os.cpu_count(),
                },
                "dataset": {"provenance": "synthetic", "rows": imported["imported"], "seed": 995},
                "model_version": predictor.load()["version"],
                "results": results,
                "process_peak_rss_mib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
                / (1024**2 if platform.system() == "Darwin" else 1024),
                "memory_note": "Process high-water RSS includes imports, setup, training when applicable, database and explanation; not idle inference RSS.",
            }
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
        print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
