import hashlib
import io
import json

import numpy as np
import pandas as pd
from sqlalchemy import select

from app.db import Dataset, Entity, Relationship, Transaction
from app.ml import FEATURES, validate_frame

IMPORT_CHUNK_SIZE = 2000
FINGERPRINT_QUERY_SIZE = 500


def inspect_dataset(frame, content):
    """Observed upload properties; provenance is a declaration, never inferred."""
    if "Class" in frame:
        repeated = frame.loc[frame.duplicated(subset=FEATURES, keep=False)]
        if len(repeated) and (repeated.groupby(FEATURES)["Class"].nunique() > 1).any():
            raise ValueError("Identical features have conflicting labels")
    return {
        "source_verification": "user-declared provenance; uploaded content is not independently authenticated",
        "csv_sha256": hashlib.sha256(content).hexdigest(),
        "input_rows": len(frame),
        "feature_count": len(FEATURES),
        "feature_names": FEATURES,
        "missing_values": int(frame.isna().sum().sum()),
        "duplicate_feature_rows": int(frame.duplicated(subset=FEATURES).sum()),
        "class_distribution": {
            str(int(key)): int(value) for key, value in frame.Class.value_counts().items()
        }
        if "Class" in frame
        else None,
        "time_range_seconds": [float(frame.Time.min()), float(frame.Time.max())],
        "amount_summary": {key: float(value) for key, value in frame.Amount.describe().items()},
        "dtypes": {column: str(dtype) for column, dtype in frame.dtypes.items()},
        "validation_policy": "finite numeric features, nonnegative Time/Amount, optional binary Class; missing inputs rejected",
    }


def ingest(session, content, name, provenance, predictor):
    if provenance not in {"ulb", "synthetic"}:
        raise ValueError("Provenance must be ulb or synthetic")
    try:
        frame = validate_frame(pd.read_csv(io.BytesIO(content)))
    except (ValueError, UnicodeDecodeError, pd.errors.ParserError) as exc:
        raise ValueError(f"Invalid CSV: {exc}") from exc
    audit = inspect_dataset(frame, content)
    unique = frame.drop_duplicates(subset=FEATURES)
    imported = 0
    model_version = None
    scoring_available = None
    model_note = "No matching trained model; import stored without scores."
    dataset = Dataset(name=name[:200], provenance=provenance, rows=0, duplicates=0, audit=audit)
    try:
        session.add(dataset)
        session.flush()
        # CSV stays one validated numeric frame. Python dicts, scores and SQL
        # parameter lists are bounded to one chunk, even on a full ULB import.
        for offset in range(0, len(unique), IMPORT_CHUNK_SIZE):
            chunk = unique.iloc[offset : offset + IMPORT_CHUNK_SIZE]
            fingerprints = [
                hashlib.sha256(
                    (provenance + json.dumps([float(value) for value in values])).encode()
                ).hexdigest()
                for values in chunk[FEATURES].itertuples(index=False, name=None)
            ]
            existing = {}
            for start in range(0, len(fingerprints), FINGERPRINT_QUERY_SIZE):
                existing.update(
                    session.execute(
                        select(Transaction.fingerprint, Transaction.label).where(
                            Transaction.fingerprint.in_(
                                fingerprints[start : start + FINGERPRINT_QUERY_SIZE]
                            )
                        )
                    ).all()
                )
            if "Class" in chunk:
                for fingerprint, label in zip(fingerprints, chunk.Class):
                    if (
                        fingerprint in existing
                        and existing[fingerprint] is not None
                        and int(label) != existing[fingerprint]
                    ):
                        raise ValueError("Uploaded label conflicts with an existing transaction")
            positions = [
                i for i, fingerprint in enumerate(fingerprints) if fingerprint not in existing
            ]
            if not positions:
                continue
            chunk = chunk.iloc[positions]
            fingerprints = [fingerprints[i] for i in positions]
            bundle, scores = None, None
            try:
                bundle, scores = predictor.predict(chunk, provenance)
            except (FileNotFoundError, ValueError):
                if model_version is not None:
                    raise ValueError(
                        "Active model changed during import; retry the complete upload"
                    ) from None
            current_availability = bundle is not None
            if scoring_available is not None and scoring_available != current_availability:
                raise ValueError("Active model changed during import; retry the complete upload")
            scoring_available = current_availability
            if bundle is not None:
                if model_version is not None and model_version != bundle["version"]:
                    raise ValueError(
                        "Active model changed during import; retry the complete upload"
                    )
                model_version = bundle["version"]
                scores = np.asarray(scores, dtype=float)
                if (
                    scores.shape != (len(chunk),)
                    or not np.isfinite(scores).all()
                    or ((scores < 0) | (scores > 1)).any()
                ):
                    raise ValueError("Model returned invalid fraud scores")
                model_note = "Scored with matching active model."
            records = []
            labels = chunk.Class.to_numpy() if "Class" in chunk else [None] * len(chunk)
            for i, values in enumerate(chunk[FEATURES].itertuples(index=False, name=None)):
                features = {feature: float(value) for feature, value in zip(FEATURES, values)}
                score = float(scores[i]) if scores is not None else None
                records.append(
                    {
                        "dataset_id": dataset.id,
                        "fingerprint": fingerprints[i],
                        "features": features,
                        "amount": features["Amount"],
                        "time": features["Time"],
                        "label": int(labels[i]) if labels[i] is not None else None,
                        "risk_score": score,
                        "flagged": int(score >= bundle["threshold"]) if bundle else None,
                        "threshold": bundle["threshold"] if bundle else None,
                        "model_version": bundle["version"] if bundle else None,
                    }
                )
            session.execute(Transaction.__table__.insert(), records)
            imported += len(records)
        dataset.rows = imported
        dataset.duplicates = len(frame) - imported
        session.commit()
    except Exception:
        # Import is atomic: neither partial transactions nor orphan audit rows
        # survive malformed scores, conflicting labels or concurrent duplicates.
        session.rollback()
        raise
    return {
        "dataset_id": dataset.id,
        "imported": imported,
        "duplicates": len(frame) - imported,
        "provenance": provenance,
        "model_note": model_note,
        "audit": audit,
    }


def seed_graph(session):
    if session.scalar(select(Entity.id).limit(1)):
        return
    entities, edges = {}, []

    def entity(id, kind):
        entities[id] = Entity(id=id, kind=kind, label=id.replace("-", " ").title())
        return id

    def edge(source, target, kind):
        edges.append(Relationship(source=source, target=target, kind=kind))

    for i in range(1, 7):
        account, card = entity(f"account-{i}", "Account"), entity(f"card-{i}", "Card")
        device = entity(f"device-{1 if i < 4 else i}", "Device")
        merchant = entity(f"merchant-{i % 3 + 1}", "Merchant")
        edge(account, card, "owns")
        edge(account, device, "uses")
        for j in range(2):
            tx = entity(f"synthetic-tx-{i}-{j}", "Transaction")
            edge(card, tx, "initiates")
            edge(tx, merchant, "targets")
    session.add_all(entities.values())
    session.flush()
    session.add_all(edges)
    session.commit()
