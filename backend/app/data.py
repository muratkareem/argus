import hashlib
import io
import json

import pandas as pd
from sqlalchemy import select

from app.db import Dataset, Entity, Relationship, Transaction
from app.ml import FEATURES, validate_frame


def ingest(session, content, name, provenance, predictor):
    try:
        frame = validate_frame(pd.read_csv(io.BytesIO(content)))
    except (ValueError, UnicodeDecodeError, pd.errors.ParserError) as exc:
        raise ValueError(f"Invalid CSV: {exc}") from exc
    unique = frame.drop_duplicates(subset=FEATURES)
    fingerprints = [
        hashlib.sha256(
            (provenance + json.dumps([float(row[f]) for f in FEATURES])).encode()
        ).hexdigest()
        for row in unique.to_dict("records")
    ]
    # Bound IN clauses for SQLite and PostgreSQL parameter limits.
    existing = set()
    for offset in range(0, len(fingerprints), 500):
        existing.update(
            session.scalars(
                select(Transaction.fingerprint).where(
                    Transaction.fingerprint.in_(fingerprints[offset : offset + 500])
                )
            )
        )
    rows = [
        (row, fingerprint)
        for row, fingerprint in zip(unique.to_dict("records"), fingerprints)
        if fingerprint not in existing
    ]
    duplicates = len(frame) - len(rows)
    dataset = Dataset(name=name[:200], provenance=provenance, rows=len(rows), duplicates=duplicates)
    session.add(dataset)
    session.flush()
    bundle, scores = None, None
    model_note = "No matching trained model; import stored without scores."
    if rows:
        try:
            bundle, scores = predictor.predict(pd.DataFrame([r for r, _ in rows]), provenance)
            model_note = "Scored with matching active model."
        except (FileNotFoundError, ValueError):
            pass
    records = []
    for i, (row, fingerprint) in enumerate(rows):
        score = float(scores[i]) if scores is not None else None
        records.append(
            {
                "dataset_id": dataset.id,
                "fingerprint": fingerprint,
                "features": {f: float(row[f]) for f in FEATURES},
                "amount": float(row["Amount"]),
                "time": float(row["Time"]),
                "label": int(row["Class"]) if "Class" in row else None,
                "risk_score": score,
                "flagged": int(score >= bundle["threshold"]) if bundle else None,
                "threshold": bundle["threshold"] if bundle else None,
                "model_version": bundle["version"] if bundle else None,
            }
        )
    if records:
        session.execute(Transaction.__table__.insert(), records)
    session.commit()
    return {
        "dataset_id": dataset.id,
        "imported": len(rows),
        "duplicates": duplicates,
        "provenance": provenance,
        "model_note": model_note,
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
