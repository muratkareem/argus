"""Train locally; load only trusted, server-owned joblib artifacts."""

import argparse
import hashlib
import json
import os
import pickle
import platform
import sys
import tempfile
import time
from collections import OrderedDict
from copy import deepcopy
from datetime import datetime, timezone
from importlib.metadata import version as package_version
from pathlib import Path
from threading import RLock

import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.calibration import calibration_curve
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    average_precision_score,
    brier_score_loss,
    confusion_matrix,
    f1_score,
    precision_recall_curve,
    precision_score,
    recall_score,
    roc_auc_score,
    roc_curve,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from xgboost import XGBClassifier

FEATURES = ["Time", *[f"V{i}" for i in range(1, 29)], "Amount"]
SEED = 42


def validate_frame(df: pd.DataFrame, require_label=False):
    if not df.columns.is_unique:
        raise ValueError("Duplicate column names are not permitted")
    missing = set(FEATURES + (["Class"] if require_label else [])) - set(df.columns)
    if missing:
        raise ValueError(f"Missing columns: {', '.join(sorted(missing))}")
    extra = set(df.columns) - set(FEATURES + ["Class"])
    if extra:
        raise ValueError(f"Unsupported columns: {', '.join(sorted(extra))}")
    if len(df) == 0:
        raise ValueError("Dataset is empty")
    out = df.copy()
    for col in out.columns:
        out[col] = pd.to_numeric(out[col], errors="raise")
    if not np.isfinite(out.to_numpy(dtype=float)).all():
        raise ValueError("Missing or non-finite values are not permitted")
    if (out[["Time", "Amount"]] < 0).any().any():
        raise ValueError("Time and Amount must be nonnegative")
    if "Class" in out and not out["Class"].isin([0, 1]).all():
        raise ValueError("Class must be binary (0 or 1)")
    # Stable feature order and numeric types make hashes and model inputs independent
    # of CSV column ordering and inferred integer/float representation.
    out = out[FEATURES + (["Class"] if "Class" in out else [])]
    out[FEATURES] = out[FEATURES].astype("float64")
    if "Class" in out:
        out["Class"] = out["Class"].astype("int8")
    return out


def partition_indices(df, split="stratified", seed=SEED):
    """Return disjoint 60/20/20 partitions without fitting any transformation."""
    if split not in {"stratified", "chronological"}:
        raise ValueError("split must be stratified or chronological")
    indices = np.arange(len(df))
    if split == "chronological":
        indices = df.sort_values("Time", kind="stable").index.to_numpy()
        first = df.loc[indices[int(len(df) * 0.6)], "Time"]
        second = df.loc[indices[int(len(df) * 0.8)], "Time"]
        partitions = (
            df.index[df.Time < first].to_numpy(),
            df.index[(df.Time >= first) & (df.Time < second)].to_numpy(),
            df.index[df.Time >= second].to_numpy(),
        )
    else:
        train_idx, rest = train_test_split(
            indices, test_size=0.4, stratify=df.Class, random_state=seed
        )
        val_idx, test_idx = train_test_split(
            rest, test_size=0.5, stratify=df.Class.iloc[rest], random_state=seed
        )
        partitions = (train_idx, val_idx, test_idx)
    for idx in partitions:
        if df.Class.iloc[idx].nunique() != 2:
            raise ValueError(
                "Every partition must contain both classes; chronological split is unsuitable"
            )
    return partitions


def synthetic(n=2000, seed=SEED):
    """ULB-shaped artificial fixture, never a substitute for ULB evaluation."""
    rng = np.random.default_rng(seed)
    y = rng.binomial(1, 0.06, n)
    x = rng.normal(size=(n, 28))
    x[:, 3] += y * 2.8
    x[:, 13] -= y * 3.5
    x[:, 16] -= y * 2.5
    df = pd.DataFrame(x, columns=FEATURES[1:-1])
    df["Time"] = np.sort(rng.uniform(0, 172800, n))
    df["Amount"] = rng.lognormal(3.4 + y * 0.4, 1.2, n).round(2)
    df["Class"] = y
    return df[FEATURES + ["Class"]]


def metrics(y, scores, threshold):
    scores = np.asarray(scores, dtype=float)
    if not np.isfinite(threshold) or not 0 <= threshold <= 1:
        raise ValueError("Decision threshold must be finite and between 0 and 1")
    if scores.ndim != 1 or len(scores) != len(y):
        raise ValueError("Scores must contain one value per label")
    if not np.isfinite(scores).all() or ((scores < 0) | (scores > 1)).any():
        raise ValueError("Scores must be finite and between 0 and 1")
    pred = scores >= threshold
    tn, fp, fn, tp = confusion_matrix(y, pred, labels=[0, 1]).ravel()
    p, r, _ = precision_recall_curve(y, scores)
    changes = np.flatnonzero(np.diff(r))
    curve_indices = np.unique(np.r_[0, changes, changes + 1, len(r) - 1])
    curve_indices = curve_indices[
        np.linspace(0, len(curve_indices) - 1, min(len(curve_indices), 400), dtype=int)
    ]
    false_positive, true_positive, _ = roc_curve(y, scores)
    roc_indices = np.linspace(0, len(false_positive) - 1, min(len(false_positive), 400), dtype=int)
    observed, predicted = calibration_curve(y, scores, n_bins=10, strategy="quantile")
    return {
        "precision": float(precision_score(y, pred, zero_division=0)),
        "recall": float(recall_score(y, pred, zero_division=0)),
        "f1": float(f1_score(y, pred, zero_division=0)),
        "average_precision": float(average_precision_score(y, scores)),
        "roc_auc": float(roc_auc_score(y, scores)),
        "false_positive_rate": float(fp / max(tn + fp, 1)),
        "false_negative_rate": float(fn / max(fn + tp, 1)),
        "brier_score": float(brier_score_loss(y, scores)),
        "calibration_curve": [
            {"mean_predicted_probability": float(a), "fraction_positive": float(b)}
            for a, b in zip(predicted, observed)
        ],
        "roc_curve": [
            {"false_positive_rate": float(a), "true_positive_rate": float(b)}
            for a, b in zip(false_positive[roc_indices], true_positive[roc_indices])
        ],
        "confusion_matrix": [[int(tn), int(fp)], [int(fn), int(tp)]],
        "pr_curve": [
            {"recall": float(a), "precision": float(b)}
            for a, b in zip(r[curve_indices], p[curve_indices])
        ],
    }


def select_threshold(y, scores):
    """Maximize validation F1; stable ties choose the lower threshold (higher recall)."""
    precision, recall, thresholds = precision_recall_curve(y, scores)
    f1 = 2 * precision[:-1] * recall[:-1] / np.maximum(precision[:-1] + recall[:-1], 1e-12)
    return float(thresholds[int(np.argmax(f1))])


def threshold_analysis(
    y, scores, selected_threshold, false_positive_cost=1.0, false_negative_cost=25.0
):
    """Illustrative costs in arbitrary units, computed on validation data only."""
    costs = np.asarray([false_positive_cost, false_negative_cost], dtype=float)
    if not np.isfinite(costs).all() or (costs < 0).any():
        raise ValueError("Classification costs must be finite and nonnegative")
    rows = []
    for threshold in np.unique(np.r_[np.linspace(0, 1, 21), selected_threshold]):
        predicted = np.asarray(scores) >= threshold
        tn, fp, fn, tp = confusion_matrix(y, predicted, labels=[0, 1]).ravel()
        rows.append(
            {
                "threshold": float(threshold),
                "precision": float(tp / max(tp + fp, 1)),
                "recall": float(tp / max(tp + fn, 1)),
                "f1": float(2 * tp / max(2 * tp + fp + fn, 1)),
                "false_positives": int(fp),
                "false_negatives": int(fn),
                "estimated_cost": float(fp * false_positive_cost + fn * false_negative_cost),
            }
        )
    return {
        "partition": "validation",
        "selection_objective": "maximum F1; cost illustration does not select the threshold",
        "cost_assumptions": {
            "unit": "arbitrary illustrative units; not monetary savings",
            "false_positive": float(false_positive_cost),
            "false_negative": float(false_negative_cost),
            "true_positive": 0,
            "true_negative": 0,
        },
        "points": rows,
    }


def dataset_audit(frame):
    """Summarize observed input; no cardholder/merchant attributes are invented."""
    return {
        "feature_schema": FEATURES,
        "target": "Class",
        "dtypes": {column: str(dtype) for column, dtype in frame.dtypes.items()},
        "missing_values": {column: int(value) for column, value in frame.isna().sum().items()},
        "missing_value_policy": "Reject missing/nonfinite input; no fitted imputation",
        "class_counts": {
            str(label): int(count) for label, count in frame.Class.value_counts().items()
        },
        "fraud_fraction": float(frame.Class.mean()),
        "amount": {
            str(key): float(value)
            for key, value in frame.Amount.describe(percentiles=[0.5, 0.9, 0.99]).items()
        },
        "time": {"minimum": float(frame.Time.min()), "maximum": float(frame.Time.max())},
        "relationships": "No account, cardholder, merchant, device or geography identifiers exist",
        "feature_meanings": {
            "Time": "Seconds elapsed from first source transaction; synthetic fixtures use an artificial clock",
            "Amount": "Nonnegative transaction amount; currency is not inferred",
            "V1-V28": "Anonymized components; semantic labels are unavailable",
            "Class": "1 fraud, 0 legitimate (declared ground truth)",
        },
    }


def inference_latency(model, frame, repeats=20):
    """Warm, sequential in-process timings; validation/API/network are excluded."""
    single = frame.iloc[[0]]
    batch = frame.iloc[np.arange(1000) % len(frame)]
    model.predict_proba(single)
    model.predict_proba(batch)
    singles, batches = [], []
    for _ in range(repeats):
        started = time.perf_counter()
        model.predict_proba(single)
        singles.append((time.perf_counter() - started) * 1000)
    for _ in range(5):
        started = time.perf_counter()
        model.predict_proba(batch)
        batches.append((time.perf_counter() - started) * 1000)
    return {
        "single_p50_ms": float(np.percentile(singles, 50)),
        "single_p95_ms": float(np.percentile(singles, 95)),
        "batch_1000_ms": float(np.median(batches)),
        "batch_1000_p95_ms": float(np.percentile(batches, 95)),
        "measurement": "warm predict_proba; one caller; no API, validation or network overhead",
        "single_repeats": repeats,
        "batch_repeats": 5,
        "batch_input": "validation rows, repeated if fewer than 1000; not independent performance data",
    }


def train(df, artifact_dir, provenance, split="stratified"):
    started = time.perf_counter()
    df = validate_frame(df, require_label=True)
    raw_rows = len(df)
    # Feature-identical rows cannot straddle partitions, even with conflicting labels.
    conflicts = df.groupby(FEATURES, dropna=False)["Class"].nunique()
    if (conflicts > 1).any():
        raise ValueError("Identical features have conflicting labels")
    df = df.drop_duplicates(subset=FEATURES).reset_index(drop=True)
    if len(df) < 100 or df["Class"].value_counts().min() < 12 or df["Class"].nunique() != 2:
        raise ValueError("Training needs at least 100 rows and 12 examples of each class")
    train_idx, val_idx, test_idx = partition_indices(df, split)
    x_train, y_train = df[FEATURES].iloc[train_idx], df.Class.iloc[train_idx]
    x_val, y_val = df[FEATURES].iloc[val_idx], df.Class.iloc[val_idx]
    ratio = float((y_train == 0).sum() / max((y_train == 1).sum(), 1))
    candidates = {
        "Logistic Regression": [
            make_pipeline(
                StandardScaler(),
                LogisticRegression(C=c, class_weight="balanced", max_iter=1500, random_state=SEED),
            )
            for c in (0.1, 1.0)
        ],
        "Random Forest": [
            RandomForestClassifier(
                n_estimators=100,
                max_depth=d,
                min_samples_leaf=2,
                class_weight="balanced_subsample",
                random_state=SEED,
                n_jobs=2,
            )
            for d in (6, 12)
        ],
        "XGBoost": [
            XGBClassifier(
                n_estimators=100,
                max_depth=d,
                learning_rate=0.08,
                subsample=0.9,
                colsample_bytree=0.9,
                scale_pos_weight=ratio,
                random_state=SEED,
                n_jobs=2,
                tree_method="hist",
                eval_metric="logloss",
            )
            for d in (3, 5)
        ],
    }
    winners = []
    for name, models in candidates.items():
        print(
            f"Training {name}: {len(train_idx)} train / {len(val_idx)} validation / {len(test_idx)} test rows",
            file=sys.stderr,
            flush=True,
        )
        fitted = []
        for model in models:
            model.fit(x_train, y_train)
            score = model.predict_proba(x_val)[:, 1]
            fitted.append((float(average_precision_score(y_val, score)), model, score))
        ap, model, scores = max(fitted, key=lambda item: item[0])
        threshold = select_threshold(y_val, scores)
        winners.append((name, model, threshold, ap, scores, inference_latency(model, x_val)))
    # Select algorithm using validation only, before accessing held-out test metrics.
    selected = max(winners, key=lambda item: (item[3], -item[5]["single_p95_ms"]))[0]
    digest = hashlib.sha256(
        pd.util.hash_pandas_object(df, index=False).values.tobytes()
    ).hexdigest()
    version = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ") + "-" + digest[:8]
    reports, best_model, best_threshold = [], None, None
    for name, model, threshold, ap, validation_scores, latency in winners:
        test_scores = model.predict_proba(df[FEATURES].iloc[test_idx])[:, 1]
        estimator = model.steps[-1][1] if hasattr(model, "steps") else model
        importance = (
            np.abs(estimator.coef_[0])
            if hasattr(estimator, "coef_")
            else estimator.feature_importances_
        )
        reports.append(
            {
                "name": name,
                "threshold": threshold,
                "validation_average_precision": ap,
                "inference_latency": latency,
                "validation": metrics(y_val, validation_scores, threshold),
                "validation_threshold_analysis": threshold_analysis(
                    y_val, validation_scores, threshold
                ),
                "test": metrics(df.Class.iloc[test_idx], test_scores, threshold),
                "parameters": {
                    k: (None if isinstance(v, float) and not np.isfinite(v) else v)
                    for k, v in estimator.get_params().items()
                    if isinstance(v, (str, int, float, bool, type(None)))
                },
                "feature_importance": sorted(
                    [{"feature": f, "importance": float(v)} for f, v in zip(FEATURES, importance)],
                    key=lambda x: x["importance"],
                    reverse=True,
                ),
            }
        )
        if name == selected:
            best_model, best_threshold = model, threshold
    report = {
        "report_schema_version": 2,
        "version": version,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "provenance": provenance,
        "split": split,
        "seed": SEED,
        "dataset_sha256": digest,
        "raw_rows": raw_rows,
        "duplicates_removed": raw_rows - len(df),
        "rows": len(df),
        "fraud_rows": int(df.Class.sum()),
        "dataset_audit": dataset_audit(df),
        "partitions": {
            k: {
                "rows": len(idx),
                "fraud": int(df.Class.iloc[idx].sum()),
                "time_minimum": float(df.Time.iloc[idx].min()),
                "time_maximum": float(df.Time.iloc[idx].max()),
                "fingerprints_sha256": hashlib.sha256(idx.tobytes()).hexdigest(),
            }
            for k, idx in [("train", train_idx), ("validation", val_idx), ("test", test_idx)]
        },
        "selected_model": selected,
        "selection_metric": "validation_average_precision",
        "selection_rationale": "Highest validation average precision; exact ties prefer lower warm single-prediction p95. Threshold maximizes validation F1. Illustrative costs are not a validated business policy.",
        "models": reports,
        "duration_seconds": round(time.perf_counter() - started, 3),
        "environment": {
            "python": platform.python_version(),
            "sklearn": sklearn.__version__,
            "numpy": np.__version__,
            "operating_system": platform.platform(),
            "machine": platform.machine(),
            "logical_cpus": os.cpu_count(),
            **{name: package_version(name) for name in ["pandas", "xgboost", "shap", "joblib"]},
        },
        "limitations": "Uncalibrated research scores. Synthetic results are not ULB benchmark results. Anonymized features cannot explain merchant or geographic behavior.",
    }
    path = Path(artifact_dir)
    path.mkdir(parents=True, exist_ok=True)
    # Immutable version directories; the small manifest is the atomic activation point.
    version_dir = path / version
    version_dir.mkdir()
    joblib.dump(
        {
            "model": best_model,
            "threshold": best_threshold,
            "version": version,
            "provenance": provenance,
            "background": x_train.iloc[:100],
            "model_name": selected,
            "feature_schema": FEATURES,
            "score_type": "uncalibrated model probability estimate",
        },
        version_dir / "model.joblib",
    )
    (version_dir / "report.json").write_text(json.dumps(report, indent=2, allow_nan=False))
    model_path = version_dir / "model.joblib"
    with model_path.open("rb") as model_file:
        model_checksum = hashlib.file_digest(model_file, "sha256").hexdigest()
    # A unique temporary name allows independent training processes to finish
    # without sharing a partial manifest. Activation is one atomic rename.
    with tempfile.NamedTemporaryFile(
        "w", dir=path, prefix="current-", suffix=".tmp", delete=False
    ) as temp:
        json.dump(
            {"version": version, "model_sha256": model_checksum, "artifact_format_version": 2}, temp
        )
        manifest_path = Path(temp.name)
    manifest_path.replace(path / "current.json")
    return report


class Predictor:
    def __init__(self, directory):
        self.directory = Path(directory)
        self.bundle = None
        self.version = None
        self._manifest_signature = None
        self._lock = RLock()
        self._explain_lock = RLock()
        self._explainer = None
        self._explainer_version = None
        self._explanations = OrderedDict()

    def load(self):
        with self._lock:
            manifest_path = self.directory / "current.json"
            stat = manifest_path.stat()
            signature = (stat.st_mtime_ns, stat.st_size, stat.st_ino)
            if self.bundle is not None and signature == self._manifest_signature:
                return self.bundle
            try:
                manifest = json.loads(manifest_path.read_text())
                version = manifest["version"]
                if (
                    not isinstance(version, str)
                    or not version
                    or any(c not in "0123456789TZ-abcdef" for c in version)
                ):
                    raise ValueError("Invalid server-owned artifact version")
                if version != self.version:
                    model_path = self.directory / version / "model.joblib"
                    if not model_path.resolve().is_relative_to(self.directory.resolve()):
                        raise ValueError(
                            "Model artifact must remain inside the server-owned directory"
                        )
                    checksum = manifest.get("model_sha256")
                    if checksum:
                        with model_path.open("rb") as model_file:
                            actual = hashlib.file_digest(model_file, "sha256").hexdigest()
                        if actual != checksum:
                            raise ValueError(
                                "Model artifact checksum mismatch; retrain or restore trusted artifacts"
                            )
                    bundle = joblib.load(model_path)
                    if bundle.get("version") != version:
                        raise ValueError("Model and manifest versions differ")
                    if bundle.get("feature_schema", FEATURES) != FEATURES:
                        raise ValueError("Model feature schema differs from this application")
                    threshold = bundle["threshold"]
                    if not np.isfinite(threshold) or not 0 <= threshold <= 1:
                        raise ValueError("Invalid artifact decision threshold")
                    if not hasattr(bundle["model"], "predict_proba"):
                        raise ValueError("Artifact does not contain a supported classifier")
                    if list(bundle["model"].classes_) != [0, 1]:
                        raise ValueError("Classifier must use binary class order [0, 1]")
                    columns = getattr(bundle["model"], "feature_names_in_", FEATURES)
                    if list(columns) != FEATURES:
                        raise ValueError(
                            "Classifier feature order differs from the required schema"
                        )
                    self.bundle, self.version = bundle, version
                self._manifest_signature = signature
            except (KeyError, TypeError, AttributeError, EOFError, pickle.UnpicklingError) as exc:
                raise ValueError(
                    "Invalid model artifact; retrain or restore trusted artifacts"
                ) from exc
            return self.bundle

    def predict(self, frame, provenance):
        frame = validate_frame(frame)
        bundle = self.load()
        if bundle["provenance"] != provenance:
            raise ValueError(
                f"Active model trained on {bundle['provenance']}; cannot score {provenance} data"
            )
        scores = np.asarray(bundle["model"].predict_proba(frame[FEATURES])[:, 1], dtype=float)
        if (
            scores.shape != (len(frame),)
            or not np.isfinite(scores).all()
            or ((scores < 0) | (scores > 1)).any()
        ):
            raise ValueError("Classifier returned invalid probability estimates")
        return bundle, scores

    def explain(self, features, provenance):
        frame = validate_frame(pd.DataFrame([features]))[FEATURES]
        bundle, scores = self.predict(frame, provenance)
        key = (bundle["version"], provenance, tuple(frame.iloc[0]))
        # SHAP has its own lock: expensive explanation work must not hold the
        # activation lock used by ordinary predictions.
        with self._explain_lock:
            if self._explainer_version != bundle["version"]:
                self._explainer = None
                self._explanations.clear()
                self._explainer_version = bundle["version"]
            if key in self._explanations:
                self._explanations.move_to_end(key)
                result = deepcopy(self._explanations[key])
                result["cache_hit"] = True
                return result
            result = self._explain(bundle, scores, frame)
            self._explanations[key] = deepcopy(result)
            if len(self._explanations) > 128:
                self._explanations.popitem(last=False)
            return result

    def _explain(self, bundle, scores, frame):
        import shap

        model = bundle["model"]
        if hasattr(model, "steps"):
            scaler, estimator = model.steps[0][1], model.steps[-1][1]
            if self._explainer is None:
                background = scaler.transform(bundle["background"])
                self._explainer = shap.LinearExplainer(estimator, background)
            explainer = self._explainer
            values = explainer.shap_values(scaler.transform(frame))[0]
            base = float(np.asarray(explainer.expected_value).reshape(-1)[0])
            output_space = "log-odds"
        else:
            if self._explainer is None:
                self._explainer = shap.TreeExplainer(model)
            explainer = self._explainer
            result = explainer(frame)
            values = result.values[0]
            if values.ndim == 2:
                values = values[:, 1]
            base_values = np.asarray(result.base_values[0]).reshape(-1)
            base = float(base_values[-1])
            output_space = (
                "probability" if isinstance(model, RandomForestClassifier) else "log-odds"
            )
        raw = float(base + np.sum(values))
        reconstructed = (
            raw
            if output_space == "probability"
            else float(1 / (1 + np.exp(np.clip(-raw, -709, 709))))
        )
        return {
            "method": "SHAP",
            "output_space": output_space,
            "base_value": base,
            "model_version": bundle["version"],
            "model_name": bundle.get("model_name", type(model).__name__),
            "risk_score": float(scores[0]),
            "reconstructed_score": reconstructed,
            "additivity_error": abs(reconstructed - float(scores[0])),
            "cache_hit": False,
            "features": sorted(
                [
                    {"feature": f, "value": float(frame[f].iloc[0]), "contribution": float(v)}
                    for f, v in zip(FEATURES, values)
                ],
                key=lambda x: abs(x["contribution"]),
                reverse=True,
            ),
            "caveat": "Contributions describe model associations, not causes. V1–V28 are anonymized; no merchant, location, or behavioral meaning is inferred. Probability-space forest contributions explain an uncalibrated score.",
        }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", type=Path)
    parser.add_argument("--synthetic", action="store_true")
    parser.add_argument("--out", type=Path, default=Path("ml/artifacts"))
    parser.add_argument("--split", choices=["stratified", "chronological"], default="stratified")
    args = parser.parse_args()
    if bool(args.csv) == args.synthetic:
        parser.error("Choose exactly one of --csv or --synthetic")
    report = train(
        synthetic() if args.synthetic else pd.read_csv(args.csv),
        args.out,
        "synthetic" if args.synthetic else "ulb",
        args.split,
    )
    print(
        json.dumps(
            {
                "version": report["version"],
                "selected_model": report["selected_model"],
                "provenance": report["provenance"],
            }
        )
    )


if __name__ == "__main__":
    main()
