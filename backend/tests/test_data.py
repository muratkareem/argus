import numpy as np
import pandas as pd
import pytest
from app.data import IMPORT_CHUNK_SIZE, ingest
from app.db import Dataset, Transaction, connect, migrate
from app.ml import FEATURES, synthetic
from sqlalchemy import func, select


class FakePredictor:
    def __init__(self):
        self.batch_sizes = []

    def predict(self, frame, provenance):
        self.batch_sizes.append(len(frame))
        return {"version": "fixture-model", "threshold": 0.5}, np.full(len(frame), 0.3)


@pytest.fixture
def session(tmp_path):
    engine, factory = connect(f"sqlite:///{tmp_path}/import.db")
    migrate(engine)
    try:
        with factory() as session:
            yield session
    finally:
        engine.dispose()


def csv(frame):
    return frame.to_csv(index=False).encode()


def test_import_bounds_prediction_batches_and_records_real_audit(session):
    frame = synthetic(IMPORT_CHUNK_SIZE + 3, seed=905)
    predictor = FakePredictor()
    result = ingest(session, csv(frame), "Fixture", "synthetic", predictor)
    assert result["imported"] == len(frame)
    assert predictor.batch_sizes == [IMPORT_CHUNK_SIZE, 3]
    audit = session.get(Dataset, result["dataset_id"]).audit
    assert audit == result["audit"]
    assert audit["class_distribution"] == {
        str(int(key)): int(value) for key, value in frame.Class.value_counts().items()
    }
    assert audit["feature_names"] == FEATURES
    assert audit["missing_values"] == 0 and audit["duplicate_feature_rows"] == 0
    assert audit["amount_summary"]["max"] == pytest.approx(frame.Amount.max())
    assert "user-declared" in audit["source_verification"]
    assert session.scalar(select(func.count(Transaction.id))) == len(frame)


def test_import_deduplicates_within_and_across_uploads_without_inventing_labels(session):
    frame = synthetic(5, seed=906)
    repeated = pd.concat([frame, frame.iloc[:2]], ignore_index=True)
    first = ingest(
        session, csv(repeated.drop(columns="Class")), "Unlabelled", "ulb", FakePredictor()
    )
    assert first["imported"] == 5 and first["duplicates"] == 2
    assert first["audit"]["class_distribution"] is None
    assert first["audit"]["duplicate_feature_rows"] == 2
    second = ingest(session, csv(frame), "Repeated", "ulb", FakePredictor())
    assert second["imported"] == 0 and second["duplicates"] == 5
    assert all(label is None for label in session.scalars(select(Transaction.label)))


def test_import_rejects_conflicting_duplicate_labels_before_any_write(session):
    frame = synthetic(2, seed=907)
    conflict = frame.iloc[:1].copy()
    conflict["Class"] = 1 - conflict.Class
    with pytest.raises(ValueError, match="conflicting labels"):
        ingest(session, csv(pd.concat([frame, conflict])), "Conflict", "synthetic", FakePredictor())
    assert session.scalar(select(func.count(Dataset.id))) == 0
    ingest(session, csv(frame), "Original", "synthetic", FakePredictor())
    with pytest.raises(ValueError, match="conflicts with an existing"):
        ingest(session, csv(conflict), "Conflict again", "synthetic", FakePredictor())
    assert session.scalar(select(func.count(Dataset.id))) == 1
    assert session.scalar(select(func.count(Transaction.id))) == 2


def test_import_failure_rolls_back_prior_chunks_and_dataset_metadata(session):
    class BrokenPredictor(FakePredictor):
        def predict(self, frame, provenance):
            if self.batch_sizes:
                raise RuntimeError("simulated late inference failure")
            return super().predict(frame, provenance)

    with pytest.raises(RuntimeError, match="late inference"):
        ingest(
            session, csv(synthetic(IMPORT_CHUNK_SIZE + 1)), "Atomic", "synthetic", BrokenPredictor()
        )
    assert session.scalar(select(func.count(Transaction.id))) == 0
    assert session.scalar(select(func.count(Dataset.id))) == 0
    assert (
        ingest(session, csv(synthetic(3)), "Recovery", "synthetic", FakePredictor())["imported"]
        == 3
    )


@pytest.mark.parametrize("scores", [[float("nan")], [1.1], [-0.1], [0.3, 0.4]])
def test_import_rejects_invalid_model_output_atomically(session, scores):
    class InvalidPredictor:
        def predict(self, frame, provenance):
            return {"version": "invalid", "threshold": 0.5}, scores

    with pytest.raises(ValueError, match="invalid fraud scores"):
        ingest(session, csv(synthetic(1)), "Bad score", "synthetic", InvalidPredictor())
    assert session.scalar(select(func.count(Transaction.id))) == 0
    assert session.scalar(select(func.count(Dataset.id))) == 0


def test_import_preserves_unscored_rows_when_model_is_unavailable(session):
    class MissingPredictor:
        def predict(self, frame, provenance):
            raise FileNotFoundError("No trained model")

    result = ingest(session, csv(synthetic(3)), "No model", "synthetic", MissingPredictor())
    assert result["imported"] == 3
    assert all(score is None for score in session.scalars(select(Transaction.risk_score)))
    assert "without scores" in result["model_note"]
