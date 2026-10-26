"""Explicit synthetic setup, with disjoint training and demonstration seeds."""

from app.config import Settings
from app.data import ingest, seed_graph
from app.db import Base, connect
from app.ml import Predictor, synthetic, train

settings = Settings()
report = train(synthetic(2000, seed=42), settings.artifact_dir, "synthetic")
engine, factory = connect(settings.database_url)
Base.metadata.create_all(engine)
with factory() as session:
    result = ingest(
        session,
        synthetic(600, seed=2026).to_csv(index=False).encode(),
        "Synthetic demonstration · independent seed 2026",
        "synthetic",
        Predictor(settings.artifact_dir),
    )
    seed_graph(session)
print({"model": report["selected_model"], "version": report["version"], "import": result})
