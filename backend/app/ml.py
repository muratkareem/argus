"""Train locally; load only trusted, server-owned joblib artifacts."""

import argparse
import hashlib
import json
import platform
import sys
import time
from datetime import datetime, timezone
from importlib.metadata import version as package_version
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    average_precision_score,
    confusion_matrix,
    f1_score,
    precision_recall_curve,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from xgboost import XGBClassifier

FEATURES = ["Time", *[f"V{i}" for i in range(1, 29)], "Amount"]
SEED = 42


def validate_frame(df: pd.DataFrame, require_label=False):
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
    return out


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
    pred = scores >= threshold
    tn, fp, fn, tp = confusion_matrix(y, pred, labels=[0, 1]).ravel()
    p, r, _ = precision_recall_curve(y, scores)
    changes = np.flatnonzero(np.diff(r))
    curve_indices = np.unique(np.r_[0, changes, changes + 1, len(r) - 1])
    curve_indices = curve_indices[
        np.linspace(0, len(curve_indices) - 1, min(len(curve_indices), 400), dtype=int)
    ]
    return {
        "precision": float(precision_score(y, pred, zero_division=0)),
        "recall": float(recall_score(y, pred, zero_division=0)),
        "f1": float(f1_score(y, pred, zero_division=0)),
        "average_precision": float(average_precision_score(y, scores)),
        "roc_auc": float(roc_auc_score(y, scores)),
        "false_positive_rate": float(fp / max(tn + fp, 1)),
        "confusion_matrix": [[int(tn), int(fp)], [int(fn), int(tp)]],
        "pr_curve": [
            {"recall": float(a), "precision": float(b)}
            for a, b in zip(r[curve_indices], p[curve_indices])
        ],
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
    indices = np.arange(len(df))
    if split == "chronological":
        indices = df.sort_values("Time", kind="stable").index.to_numpy()
        # Equal timestamps belong to one partition to prevent temporal overlap.
        first = df.loc[indices[int(len(df) * 0.6)], "Time"]
        second = df.loc[indices[int(len(df) * 0.8)], "Time"]
        train_idx = df.index[df.Time < first].to_numpy()
        val_idx = df.index[(df.Time >= first) & (df.Time < second)].to_numpy()
        test_idx = df.index[df.Time >= second].to_numpy()
    else:
        train_idx, rest = train_test_split(
            indices, test_size=0.4, stratify=df.Class, random_state=SEED
        )
        val_idx, test_idx = train_test_split(
            rest, test_size=0.5, stratify=df.Class.iloc[rest], random_state=SEED
        )
    for idx in (train_idx, val_idx, test_idx):
        if df.Class.iloc[idx].nunique() != 2:
            raise ValueError(
                "Every partition must contain both classes; chronological split is unsuitable"
            )
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
        p, r, thresholds = precision_recall_curve(y_val, scores)
        f1 = 2 * p[:-1] * r[:-1] / np.maximum(p[:-1] + r[:-1], 1e-12)
        threshold = float(thresholds[int(np.argmax(f1))])
        winners.append((name, model, threshold, ap))
    # Select algorithm using validation only, before accessing held-out test metrics.
    selected = max(winners, key=lambda item: item[3])[0]
    digest = hashlib.sha256(
        pd.util.hash_pandas_object(df, index=False).values.tobytes()
    ).hexdigest()
    version = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ") + "-" + digest[:8]
    reports, best_model, best_threshold = [], None, None
    for name, model, threshold, ap in winners:
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
        "partitions": {
            k: {
                "rows": len(idx),
                "fraud": int(df.Class.iloc[idx].sum()),
                "fingerprints_sha256": hashlib.sha256(idx.tobytes()).hexdigest(),
            }
            for k, idx in [("train", train_idx), ("validation", val_idx), ("test", test_idx)]
        },
        "selected_model": selected,
        "selection_metric": "validation_average_precision",
        "models": reports,
        "duration_seconds": round(time.perf_counter() - started, 3),
        "environment": {
            "python": platform.python_version(),
            "sklearn": sklearn.__version__,
            "numpy": np.__version__,
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
        },
        version_dir / "model.joblib",
    )
    (version_dir / "report.json").write_text(json.dumps(report, indent=2, allow_nan=False))
    temp = path / "current.tmp"
    temp.write_text(json.dumps({"version": version}))
    temp.replace(path / "current.json")
    return report


class Predictor:
    def __init__(self, directory):
        self.directory = Path(directory)
        self.bundle = None
        self.version = None

    def load(self):
        manifest = json.loads((self.directory / "current.json").read_text())
        version = manifest["version"]
        if not version or any(c not in "0123456789TZ-abcdef" for c in version):
            raise ValueError("Invalid server-owned artifact version")
        if version != self.version:
            self.bundle = joblib.load(self.directory / version / "model.joblib")
            self.version = version
        return self.bundle

    def predict(self, frame, provenance):
        bundle = self.load()
        if bundle["provenance"] != provenance:
            raise ValueError(
                f"Active model trained on {bundle['provenance']}; cannot score {provenance} data"
            )
        return bundle, bundle["model"].predict_proba(frame[FEATURES])[:, 1]

    def explain(self, features, provenance):
        import shap

        bundle, scores = self.predict(pd.DataFrame([features]), provenance)
        model = bundle["model"]
        frame = pd.DataFrame([features])[FEATURES]
        if hasattr(model, "steps"):
            scaler, estimator = model.steps[0][1], model.steps[-1][1]
            background = scaler.transform(bundle["background"])
            explainer = shap.LinearExplainer(estimator, background)
            values = explainer.shap_values(scaler.transform(frame))[0]
            base = float(np.asarray(explainer.expected_value).reshape(-1)[0])
        else:
            explainer = shap.TreeExplainer(model)
            result = explainer(frame)
            values = result.values[0]
            if values.ndim == 2:
                values = values[:, 1]
            base_values = np.asarray(result.base_values[0]).reshape(-1)
            base = float(base_values[-1])
        return {
            "method": "SHAP",
            "output_space": "raw model output (log-odds for logistic/XGBoost; probability for forest)",
            "base_value": base,
            "model_version": bundle["version"],
            "risk_score": float(scores[0]),
            "features": sorted(
                [
                    {"feature": f, "value": features[f], "contribution": float(v)}
                    for f, v in zip(FEATURES, values)
                ],
                key=lambda x: abs(x["contribution"]),
                reverse=True,
            ),
            "caveat": "V1–V28 are anonymized; no merchant, location, or behavioral meaning is inferred.",
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
