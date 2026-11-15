"""Offline external benchmarks. Never activate or replace a production ULB model."""

import argparse
import hashlib
import json
import os
import platform
import time
from datetime import datetime, timezone
from importlib.metadata import version as package_version
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score
from sklearn.pipeline import Pipeline
from xgboost import XGBClassifier

from app.benchmark_data import merge_identity, prepare, preprocessor, read_source
from app.ml import (
    SEED,
    inference_latency,
    metrics,
    partition_indices,
    select_threshold,
    threshold_analysis,
)

RESEARCH_DIR = Path(__file__).resolve().parents[2] / "docs" / "research"
DATASETS = [
    {
        "id": "ulb",
        "name": "ULB credit card transactions",
        "data_kind": "real",
        "source": "https://www.kaggle.com/datasets/mlg-ulb/creditcardfraud",
        "license": "ODbL database / DbCL contents",
        "blocker": None,
    },
    {
        "id": "ieee_cis",
        "name": "IEEE-CIS Fraud Detection",
        "data_kind": "real",
        "source": "https://www.kaggle.com/competitions/ieee-fraud-detection",
        "license": "Kaggle competition rules; noncommercial academic use; review and accept before access",
        "blocker": "Official competition download returned HTTP 401 without Kaggle authorization. "
        "Sign in, accept competition rules, then download train_transaction.csv and optionally "
        "train_identity.csv. No private test labels are available; ARGUS splits labeled training data.",
    },
    {
        "id": "paysim",
        "name": "PaySim mobile money simulation",
        "data_kind": "synthetic",
        "source": "https://www.kaggle.com/datasets/ealaxi/paysim1",
        "license": "CC BY-SA 4.0",
        "blocker": None,
    },
]


def wilson(successes, total):
    """95% Wilson binomial interval; undefined denominators return null."""
    if not total:
        return None
    z = 1.959963984540054
    p = successes / total
    denominator = 1 + z * z / total
    center = (p + z * z / (2 * total)) / denominator
    radius = z * np.sqrt(p * (1 - p) / total + z * z / (4 * total * total)) / denominator
    return [max(0.0, float(center - radius)), min(1.0, float(center + radius))]


def confidence_intervals(result):
    (_, fp), (fn, tp) = result["confusion_matrix"]
    return {
        "method": "Wilson binomial, 95%; conditional on fitted model and threshold",
        "precision": wilson(tp, tp + fp),
        "recall": wilson(tp, tp + fn),
        "limitation": "IID approximation; ignores temporal/entity dependence and training uncertainty. "
        "No F1/AP/ROC-AUC confidence intervals or paired significance claims are made.",
    }


def candidates(ratio):
    return {
        "Logistic Regression": [
            LogisticRegression(C=c, class_weight="balanced", max_iter=2000, random_state=SEED)
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


def train(frame, dataset_id, source_audit, split="chronological", identity_audit=None):
    started = time.perf_counter()
    data = prepare(frame, dataset_id)
    partition_frame = pd.DataFrame({"Time": data.time, "Class": data.y})
    indices = partition_indices(partition_frame, split)
    train_idx, val_idx, test_idx = indices
    transform = preprocessor(data)
    x_train = transform.fit_transform(data.x.iloc[train_idx])
    x_val = transform.transform(data.x.iloc[val_idx])
    y_train, y_val = data.y.iloc[train_idx], data.y.iloc[val_idx]
    ratio = float((y_train == 0).sum() / y_train.sum())
    winners, search = [], {}
    for name, estimators in candidates(ratio).items():
        print(f"Training {dataset_id}: {name} ({len(train_idx)} train rows)", flush=True)
        fitted, search[name] = [], []
        for estimator in estimators:
            estimator.fit(x_train, y_train)
            scores = estimator.predict_proba(x_val)[:, 1]
            ap = float(average_precision_score(y_val, scores))
            parameters = {
                k: v
                for k, v in estimator.get_params().items()
                if isinstance(v, (int, float, str, bool, type(None)))
                and not (isinstance(v, float) and not np.isfinite(v))
            }
            search[name].append({"parameters": parameters, "validation_average_precision": ap})
            fitted.append((ap, estimator, scores, parameters))
        ap, estimator, scores, parameters = max(fitted, key=lambda item: item[0])
        model = Pipeline([("preprocessor", transform), ("classifier", estimator)])
        latency = inference_latency(model, data.x.iloc[val_idx])
        winners.append(
            (name, model, select_threshold(y_val, scores), ap, scores, latency, parameters)
        )
    # Nothing from test is transformed, scored or used to select candidates above.
    selected = max(winners, key=lambda item: (item[3], -item[5]["single_p95_ms"]))[0]
    models = []
    feature_names = transform.get_feature_names_out()
    for name, model, threshold, ap, validation_scores, latency, parameters in winners:
        result = metrics(
            data.y.iloc[test_idx], model.predict_proba(data.x.iloc[test_idx])[:, 1], threshold
        )
        result["confidence_intervals"] = confidence_intervals(result)
        estimator = model.named_steps["classifier"]
        importance = (
            np.abs(estimator.coef_[0])
            if hasattr(estimator, "coef_")
            else estimator.feature_importances_
        )
        models.append(
            {
                "name": name,
                "threshold": threshold,
                "validation_average_precision": ap,
                "validation": metrics(y_val, validation_scores, threshold),
                "test": result,
                "validation_threshold_analysis": threshold_analysis(
                    y_val, validation_scores, threshold
                ),
                "inference_latency": latency,
                "parameters": parameters,
                "feature_importance": sorted(
                    [
                        {"feature": f, "importance": float(v)}
                        for f, v in zip(feature_names, importance)
                    ],
                    key=lambda f: f["importance"],
                    reverse=True,
                ),
            }
        )
    digest = hashlib.sha256(data.fingerprints.to_numpy().tobytes()).hexdigest()
    created_at = datetime.now(timezone.utc)
    descriptor = next(item for item in DATASETS if item["id"] == dataset_id)
    return {
        "report_schema_version": 3,
        "dataset_id": dataset_id,
        "data_kind": descriptor["data_kind"],
        "execution_status": "verified",
        "provenance": dataset_id,
        "version": dataset_id + "-" + created_at.strftime("%Y%m%dT%H%M%S%fZ") + "-" + digest[:8],
        "created_at": created_at.isoformat(),
        "seed": SEED,
        "split": split,
        "source": {**descriptor, **source_audit},
        "identity_source": identity_audit,
        "dataset_sha256": digest,
        "raw_rows": len(frame),
        "rows": len(data.x),
        "fraud_rows": int(data.y.sum()),
        "duplicates_removed": data.duplicates_removed,
        "preprocessing": {
            "numeric": data.numeric,
            "categorical": data.categorical,
            "excluded": data.excluded,
            "fit_partition": "train only",
            "one_hot_max_categories": 32,
            "numeric_missing": "training median; all-missing columns retained as zero",
            "numeric_scaling": "training StandardScaler",
            "categorical_missing": "constant missing",
            "unknown_categories": "training infrequent bucket if present, otherwise all zeros",
        },
        "partitions": {
            name: {
                "rows": len(idx),
                "fraud": int(data.y.iloc[idx].sum()),
                "time_minimum": float(data.time.iloc[idx].min()),
                "time_maximum": float(data.time.iloc[idx].max()),
                "fingerprints_sha256": hashlib.sha256(
                    data.fingerprints.iloc[idx].to_numpy().tobytes()
                ).hexdigest(),
            }
            for name, idx in zip(("train", "validation", "test"), indices)
        },
        "selected_model": selected,
        "selection_metric": "validation_average_precision",
        "selection_rationale": "Highest validation AP, ties lower warm single p95 latency; "
        "candidate AP ties keep first declared candidate. Threshold maximizes validation F1.",
        "candidate_search": search,
        "models": models,
        "duration_seconds": round(time.perf_counter() - started, 3),
        "environment": {
            "python": platform.python_version(),
            "operating_system": platform.platform(),
            "machine": platform.machine(),
            "logical_cpus": os.cpu_count(),
            **{p: package_version(p) for p in ("pandas", "numpy", "scikit-learn", "xgboost")},
        },
        "limitations": "Independent in-domain training, not cross-dataset transfer validation. "
        "Single seed; uncalibrated scores; prevalence and feature availability differ between datasets. "
        "Chronological evaluation does not isolate recurring entities. Sampling can omit rare patterns. "
        "PaySim is a simulator, not evidence of real credit card fraud performance. "
        "IEEE feature availability at decision time requires domain review.",
    }


def catalog(directory=RESEARCH_DIR):
    """Expose only explicit completed reports; absent data never gets placeholder metrics."""
    directory = Path(directory)
    reports, errors = [], []
    paths = list((directory / "benchmarks").glob("*.json"))
    paths += [directory / f"diploma-ulb-{split}.json" for split in ("stratified", "chronological")]
    for path in sorted(paths):
        if not path.exists():
            continue
        try:
            report = json.loads(path.read_text())
            legacy_ulb = path.name.startswith("diploma-ulb-")
            dataset_id = "ulb" if legacy_ulb else report["dataset_id"]
            if dataset_id not in {d["id"] for d in DATASETS}:
                raise ValueError("Unknown dataset")
            if not legacy_ulb and report.get("execution_status") != "verified":
                raise ValueError("Report is not an executed benchmark")
            if {m["name"] for m in report["models"]} != {
                "Logistic Regression",
                "Random Forest",
                "XGBoost",
            }:
                raise ValueError("Incomplete model comparison")
            if sum(p["rows"] for p in report["partitions"].values()) != report["rows"]:
                raise ValueError("Partition counts disagree")
            for model in report["models"]:
                for field in ("precision", "recall", "f1", "average_precision", "roc_auc"):
                    value = model["test"][field]
                    if (
                        not isinstance(value, (int, float))
                        or not np.isfinite(value)
                        or not 0 <= value <= 1
                    ):
                        raise ValueError("Invalid measured metric")
                if (
                    sum(map(sum, model["test"]["confusion_matrix"]))
                    != report["partitions"]["test"]["rows"]
                ):
                    raise ValueError("Confusion matrix disagrees with test size")
                model["test"]["confidence_intervals"] = confidence_intervals(model["test"])
            report.update(
                dataset_id=dataset_id,
                execution_status="verified",
                data_kind=next(d["data_kind"] for d in DATASETS if d["id"] == dataset_id),
            )
            reports.append(report)
        except (ValueError, KeyError, TypeError) as exc:
            errors.append({"file": path.name, "error": str(exc)})
    datasets = [
        {
            **item,
            "status": "evaluated"
            if any(r["dataset_id"] == item["id"] for r in reports)
            else "access_required"
            if item["blocker"]
            else "not_evaluated",
        }
        for item in DATASETS
    ]
    return {
        "datasets": datasets,
        "experiments": reports,
        "report_errors": errors,
        "interpretation": "Models are independently trained per dataset; this is not cross-dataset transfer validation.",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", choices=["paysim", "ieee_cis"], required=True)
    parser.add_argument("--csv", type=Path, required=True)
    parser.add_argument("--identity", type=Path)
    parser.add_argument("--max-rows", type=int)
    parser.add_argument("--split", choices=["stratified", "chronological"], default="chronological")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("Output already exists; refusing to overwrite a completed report")
    frame, audit = read_source(args.csv, args.max_rows)
    identity_audit = None
    if args.identity:
        if args.dataset != "ieee_cis":
            parser.error("--identity is only supported for IEEE-CIS")
        identity = pd.read_csv(args.identity, dtype=str)
        with args.identity.open("rb") as source:
            identity_audit = {
                "csv_sha256": hashlib.file_digest(source, "sha256").hexdigest(),
                "rows": len(identity),
            }
        frame = merge_identity(frame, identity)
    report = train(frame, args.dataset, audit, args.split, identity_audit)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x") as out:
        json.dump(report, out, indent=2, allow_nan=False)
        out.write("\n")
    print(
        f"Saved {args.output}; selected {report['selected_model']} by validation AP. Production unchanged."
    )


if __name__ == "__main__":
    main()
