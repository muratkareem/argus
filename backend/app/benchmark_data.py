"""Explicit offline dataset adapters. Production ULB inference remains unchanged."""

import hashlib
import re
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from app.ml import SEED

PAYSIM_COLUMNS = {
    "step",
    "type",
    "amount",
    "nameOrig",
    "oldbalanceOrg",
    "newbalanceOrig",
    "nameDest",
    "oldbalanceDest",
    "newbalanceDest",
    "isFraud",
    "isFlaggedFraud",
}
PAYSIM_TYPES = {"CASH_IN", "CASH_OUT", "DEBIT", "PAYMENT", "TRANSFER"}
IEEE_CATEGORICAL = {
    "ProductCD",
    "card1",
    "card2",
    "card3",
    "card4",
    "card5",
    "card6",
    "addr1",
    "addr2",
    "P_emaildomain",
    "R_emaildomain",
    "DeviceType",
    "DeviceInfo",
    *[f"M{i}" for i in range(1, 10)],
    *[f"id_{i}" for i in range(12, 39)],
}


@dataclass
class Prepared:
    x: pd.DataFrame
    y: pd.Series
    time: pd.Series
    fingerprints: pd.Series
    numeric: list[str]
    categorical: list[str]
    duplicates_removed: int
    excluded: list[str]


def read_source(path: Path, max_rows: int | None = None):
    """Uniform priority sample over the entire CSV, independent of labels/time."""
    if max_rows is not None and max_rows < 30:
        raise ValueError("max_rows must be at least 30")
    rng = np.random.default_rng(SEED)
    frames, priorities = [], np.empty(0)
    rows = fraud = 0
    kept = None
    for chunk in pd.read_csv(path, chunksize=100_000, dtype=str):
        if "isFraud" not in chunk or not chunk.isFraud.isin(["0", "1"]).all():
            raise ValueError("Source isFraud must contain only binary 0/1 labels")
        rows += len(chunk)
        fraud += int(chunk.isFraud.astype(int).sum())
        if max_rows is None:
            frames.append(chunk)
            continue
        priorities = np.r_[priorities, rng.random(len(chunk))]
        kept = pd.concat([kept, chunk], ignore_index=False) if kept is not None else chunk
        if len(kept) > max_rows:
            idx = np.argpartition(priorities, max_rows - 1)[:max_rows]
            kept, priorities = kept.iloc[idx], priorities[idx]
    if not rows:
        raise ValueError("Empty source CSV")
    frame = pd.concat(frames) if max_rows is None else kept.sort_index()
    with path.open("rb") as source:
        digest = hashlib.file_digest(source, "sha256").hexdigest()
    return frame.reset_index(drop=True), {
        "csv_sha256": digest,
        "csv_bytes": path.stat().st_size,
        "rows": rows,
        "fraud_rows": fraud,
        "sampling": "full dataset"
        if max_rows is None or rows <= max_rows
        else "uniform smallest independent random priorities over full source; before splitting",
        "requested_max_rows": max_rows,
        "sample_rows": len(frame),
        "seed": SEED,
    }


def merge_identity(transactions, identity):
    """Optional labeled IEEE identity join: never join Kaggle's unlabeled test set."""
    for frame in (transactions, identity):
        if "TransactionID" not in frame or frame.TransactionID.isna().any():
            raise ValueError("Identity join requires nonmissing TransactionID")
        if frame.TransactionID.duplicated().any():
            raise ValueError("TransactionID must be unique for one-to-one identity join")
    if (set(identity) & set(transactions)) != {"TransactionID"}:
        raise ValueError("Identity columns overlap transaction columns")
    return transactions.merge(identity, on="TransactionID", how="left", validate="one_to_one")


def prepare(frame, dataset_id):
    if not frame.columns.is_unique or frame.empty:
        raise ValueError("Dataset must be nonempty with unique columns")
    if "isFraud" not in frame:
        raise ValueError("Labeled training data requires isFraud")
    target = pd.to_numeric(frame.isFraud, errors="raise")
    if not target.isin([0, 1]).all():
        raise ValueError("isFraud must be binary")
    if dataset_id == "paysim":
        if set(frame) != PAYSIM_COLUMNS:
            raise ValueError("PaySim requires the official eleven-column schema")
        if not frame.type.isin(PAYSIM_TYPES).all():
            raise ValueError("Unknown PaySim transaction type")
        time_column, amount_column = "step", "amount"
    elif dataset_id == "ieee_cis":
        required = {"TransactionID", "TransactionDT", "TransactionAmt", "ProductCD", "isFraud"}
        if not required <= set(frame):
            raise ValueError("IEEE-CIS requires labeled train_transaction.csv columns")
        if frame.TransactionID.isna().any() or frame.TransactionID.duplicated().any():
            raise ValueError("IEEE-CIS TransactionID must be unique and nonmissing")
        allowed = required | IEEE_CATEGORICAL | {"dist1", "dist2"}
        unknown = {c for c in frame if c not in allowed and not re.fullmatch(r"[CDV]\d+|id_\d+", c)}
        if unknown:
            raise ValueError(f"Unsupported IEEE-CIS fields: {sorted(unknown)}")
        time_column, amount_column = "TransactionDT", "TransactionAmt"
    else:
        raise ValueError("External dataset must be ieee_cis or paysim")
    # Raw event signatures retain PaySim entity IDs for deduplication only. Distinct
    # transactions with the same amount/type must not collapse into one event.
    signature_columns = sorted(set(frame) - {"isFraud", "TransactionID"})
    fingerprints = pd.util.hash_pandas_object(frame[signature_columns], index=False)
    if (
        pd.DataFrame({"fingerprint": fingerprints, "target": target})
        .groupby("fingerprint")
        .target.nunique()
        .gt(1)
        .any()
    ):
        raise ValueError("Conflicting labels for identical transactions")
    keep = ~fingerprints.duplicated()
    raw_rows = len(frame)
    frame, target = frame.loc[keep].reset_index(drop=True), target.loc[keep].reset_index(drop=True)
    fingerprints = fingerprints.loc[keep].reset_index(drop=True)
    event_time = pd.to_numeric(frame[time_column], errors="raise").astype(float)
    amount = pd.to_numeric(frame[amount_column], errors="raise").astype(float)
    if not np.isfinite(event_time).all() or not np.isfinite(amount).all():
        raise ValueError("Time and amount must be finite")
    if (event_time < 0).any() or (amount < 0).any():
        raise ValueError("Time and amount must be nonnegative")
    if dataset_id == "paysim":
        x = pd.DataFrame({"amount": amount, "log_amount": np.log1p(amount), "type": frame.type})
        numeric, categorical = ["amount", "log_amount"], ["type"]
    else:
        x = frame.drop(columns=["isFraud", "TransactionID", "TransactionDT"]).copy()
        categorical = sorted(set(x) & IEEE_CATEGORICAL)
        numeric = sorted(set(x) - set(categorical))
        for column in numeric:
            x[column] = pd.to_numeric(x[column], errors="raise").astype(float)
            if np.isinf(x[column]).any():
                raise ValueError("Numeric predictors cannot contain infinity")
        for column in categorical:
            x[column] = x[column].map(lambda value: str(value) if pd.notna(value) else np.nan)
        x = x[numeric + categorical]
    return Prepared(
        x,
        target.astype("int8"),
        event_time,
        fingerprints,
        numeric,
        categorical,
        raw_rows - len(frame),
        sorted(set(frame) - set(x) - {"isFraud"}),
    )


def preprocessor(data):
    # No fit occurs here; train() fits this object exclusively on the train partition.
    return ColumnTransformer(
        [
            (
                "numeric",
                make_pipeline(
                    SimpleImputer(strategy="median", keep_empty_features=True), StandardScaler()
                ),
                data.numeric,
            ),
            (
                "categorical",
                make_pipeline(
                    SimpleImputer(strategy="constant", fill_value="missing"),
                    OneHotEncoder(handle_unknown="infrequent_if_exist", max_categories=32),
                ),
                data.categorical,
            ),
        ],
        sparse_threshold=1.0,
    )
