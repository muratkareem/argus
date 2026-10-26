"""Explicit, idempotent synthetic setup with independent training and demo seeds."""

import json

from app.config import Settings
from app.data import ingest, seed_graph
from app.db import Base, connect
from app.ml import Predictor, synthetic, train

settings = Settings()
predictor = Predictor(settings.artifact_dir)
if (settings.artifact_dir / "current.json").exists():
    bundle = predictor.load()
    if bundle["provenance"] != "synthetic":
        raise SystemExit(
            "Active model is not synthetic. Use a separate ARGUS_ARTIFACT_DIR for demo setup."
        )
    report = json.loads((settings.artifact_dir / bundle["version"] / "report.json").read_text())
else:
    report = train(synthetic(2000, seed=42), settings.artifact_dir, "synthetic")
engine, factory = connect(settings.database_url)
Base.metadata.create_all(engine)
with factory() as session:
    result = ingest(
        session,
        synthetic(600, seed=2026).to_csv(index=False).encode(),
        "Synthetic demonstration · independent seed 2026",
        "synthetic",
        predictor,
    )
    seed_graph(session)
print({"model": report["selected_model"], "version": report["version"], "import": result})
