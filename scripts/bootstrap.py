"""Explicit, idempotent synthetic setup with independent training and demo seeds."""

import json

from app.config import Settings
from app.data import ingest, seed_graph
from app.db import Dataset, Transaction, connect, migrate
from app.ml import Predictor, synthetic, train
from sqlalchemy import func, select

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
migrate(engine)
with factory() as session:
    existing = session.scalar(
        select(func.count())
        .select_from(Transaction)
        .join(Dataset)
        .where(Dataset.name == "Synthetic demonstration · independent seed 2026")
    )
    if existing:
        result = {"imported": 0, "existing": existing}
    else:
        result = ingest(
            session,
            synthetic(600, seed=2026).to_csv(index=False).encode(),
            "Synthetic demonstration · independent seed 2026",
            "synthetic",
            predictor,
        )
    seed_graph(session)
print({"model": report["selected_model"], "version": report["version"], "import": result})

engine.dispose()
