"""Reproducible import allocation benchmark; fake scores isolate ingestion overhead.

PYTHONPATH=backend python scripts/benchmark_ingestion.py --label baseline --output report.json
The CSV and synthetic fixture are created before the measured region. These are
single cold-database trials, not HTTP latencies or real-model speed measurements.
"""

import argparse
import hashlib
import json
import platform
import tempfile
import time
import tracemalloc
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from app.data import ingest
from app.db import connect, migrate
from app.ml import synthetic
from sqlalchemy import event


class BenchmarkPredictor:
    def predict(self, frame, provenance):
        return {"version": "benchmark-fixture", "threshold": 0.5}, np.full(len(frame), 0.25)


def measure(size):
    content = synthetic(size, seed=2026).to_csv(index=False).encode()
    with tempfile.TemporaryDirectory(prefix="argus-import-benchmark-") as directory:
        engine, factory = connect(f"sqlite:///{directory}/benchmark.db")
        migrate(engine)
        statements = []

        @event.listens_for(engine, "before_cursor_execute")
        def count_sql(_connection, _cursor, statement, _parameters, _context, _executemany):
            statements.append(statement.split()[0])

        try:
            with factory() as session:
                tracemalloc.start()
                started = time.perf_counter()
                result = ingest(
                    session, content, "Synthetic benchmark", "synthetic", BenchmarkPredictor()
                )
                elapsed = time.perf_counter() - started
                _current, peak = tracemalloc.get_traced_memory()
                tracemalloc.stop()
            return {
                "rows": size,
                "csv_sha256": hashlib.sha256(content).hexdigest(),
                "imported": result["imported"],
                "elapsed_seconds": round(elapsed, 6),
                "rows_per_second": round(size / elapsed, 3),
                "peak_traced_allocations_mib": round(peak / 1024**2, 3),
                "sql_statements": len(statements),
            }
        finally:
            engine.dispose()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--label", required=True)
    parser.add_argument("--sizes", type=int, nargs="+", default=[12000, 60000])
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = {
        "label": args.label,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "environment": {
            "platform": platform.platform(),
            "python": platform.python_version(),
            "processor": platform.processor(),
        },
        "methodology": "One trial per size; cold fresh SQLite WAL database; synthetic seed 2026; deterministic fake vector scores; tracemalloc Python allocation peak; CSV fixture generation excluded; concurrency 1. Tracing adds overhead and this is not HTTP/model throughput.",
        "measurements": [measure(size) for size in args.sizes],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    print(json.dumps(report, indent=2))
