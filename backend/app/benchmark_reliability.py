"""Conditional uncertainty and descriptive diagnostics; never selects a model."""

import argparse
import hashlib
import json
import os
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

METRICS = ("precision", "recall", "f1", "average_precision", "roc_auc")


def implementation_sha256():
    digest = hashlib.sha256()
    for name in ("benchmark_data.py", "benchmark_reliability.py", "benchmarks.py", "ml.py"):
        digest.update(name.encode())
        digest.update(Path(__file__).with_name(name).read_bytes())
    return digest.hexdigest()


def write_report(path, report):
    """Atomically publish complete JSON without overwriting a prior result."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", dir=path.parent, delete=False) as output:
            temporary = Path(output.name)
            json.dump(report, output, indent=2, allow_nan=False)
            output.write("\n")
        os.link(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def rank_metrics(positive, negative, selected):
    """Exact tied-score metrics from descending weighted label counts."""
    tp, fp = np.cumsum(positive), np.cumsum(negative)
    positives, negatives = tp[-1], fp[-1]
    at_tp = tp[selected - 1] if selected else 0.0
    at_fp = fp[selected - 1] if selected else 0.0
    alerts = at_tp + at_fp
    return {
        "precision": float(at_tp / alerts) if alerts else np.nan,
        "recall": float(at_tp / positives) if positives else np.nan,
        "f1": float(2 * at_tp / (alerts + positives)) if alerts + positives else np.nan,
        "average_precision": float(np.sum(positive * tp / np.maximum(tp + fp, 1)) / positives)
        if positives and negatives
        else np.nan,
        "roc_auc": float(np.sum((tp + np.r_[0, tp[:-1]]) * negative) / (2 * positives * negatives))
        if positives and negatives
        else np.nan,
    }


def day_bootstrap(y, scores, event_time, threshold, repeats=200, seed=20261116):
    """Resample whole simulation days; pre-sort once, retaining exact score ties."""
    if repeats < 2:
        raise ValueError("At least two bootstrap replicates are required")
    y, scores, event_time = np.asarray(y), np.asarray(scores), np.asarray(event_time)
    if len(y) == 0 or len(y) != len(scores) or len(y) != len(event_time):
        raise ValueError("Bootstrap arrays must have equal nonzero lengths")
    if not np.isin(y, [0, 1]).all() or not np.isfinite(scores).all():
        raise ValueError("Bootstrap requires binary labels and finite scores")
    days = np.floor((event_time - 1) / 24)
    _, codes = np.unique(days, return_inverse=True)
    blocks = int(codes.max()) + 1
    if blocks < 2:
        raise ValueError("At least two observed day clusters are required")
    order = np.argsort(-scores, kind="stable")
    scores, y, codes = scores[order], y[order], codes[order]
    start = np.r_[0, np.flatnonzero(np.diff(scores)) + 1]
    selected = int(np.searchsorted(-scores[start], -threshold, side="right"))
    rng = np.random.default_rng(seed)
    samples = {key: [] for key in METRICS}
    for _ in range(repeats):
        counts = np.bincount(rng.integers(0, blocks, blocks), minlength=blocks)
        weight = counts[codes]
        positive = np.add.reduceat(weight * y, start)
        negative = np.add.reduceat(weight * (1 - y), start)
        for key, value in rank_metrics(positive, negative, selected).items():
            if np.isfinite(value):
                samples[key].append(value)
    return {
        "method": "95% percentile bootstrap of observed 24-hour simulation-day clusters",
        "partition": "test; fitted estimator and validation-selected threshold frozen",
        "repeats": repeats,
        "seed": seed,
        "clusters": blocks,
        "block_hours": 24,
        "intervals": {
            key: np.quantile(values, [0.025, 0.975]).tolist() if len(values) >= 2 else None
            for key, values in samples.items()
        },
        "valid_replicates": {key: len(values) for key, values in samples.items()},
        "limitation": "Conditional approximation assuming independent days. Few/partial-day clusters, "
        "cross-day dependence and recurring entities limit coverage; training uncertainty is excluded.",
    }


def error_analysis(data, indices, scores, threshold):
    """Descriptive counts at the frozen threshold; no examples/identifiers exported."""
    y = data.y.iloc[indices].to_numpy()
    pred = np.asarray(scores) >= threshold
    frame = pd.DataFrame(
        {
            "time": data.time.iloc[indices].to_numpy(),
            "label": y,
            "amount": data.x.iloc[indices]["amount"].to_numpy(),
            "type": data.x.iloc[indices]["type"].astype(str).to_numpy(),
            "tp": y * pred,
            "fp": (1 - y) * pred,
            "fn": y * ~pred,
            "tn": (1 - y) * ~pred,
        }
    )
    by_type = []
    for name, group in frame.groupby("type", observed=True):
        by_type.append(
            {
                "type": str(name),
                "rows": len(group),
                "fraud": int(group.label.sum()),
                **{key: int(group[key].sum()) for key in ("tp", "fp", "fn", "tn")},
            }
        )
    amounts = {}
    for key in ("tp", "fp", "fn", "tn"):
        values = frame.loc[frame[key].astype(bool), "amount"]
        amounts[key] = {
            "rows": len(values),
            "amount_quantiles": {
                str(q): float(values.quantile(q)) for q in (0.0, 0.25, 0.5, 0.75, 1.0)
            }
            if len(values)
            else {},
        }
    return {
        "threshold": threshold,
        "by_type": by_type,
        "error_groups": amounts,
        "interpretation": "Descriptive test error analysis only; no feature or threshold retuning.",
    }


def temporal_audit(data, indices):
    hours = data.time.iloc[indices].to_numpy()
    labels = data.y.iloc[indices].to_numpy()
    frame = pd.DataFrame({"hour": hours, "fraud": labels})
    table = frame.groupby("hour", sort=True).fraud.agg(["size", "sum"])
    return [
        {
            "hour": float(hour),
            "rows": int(row["size"]),
            "fraud": int(row["sum"]),
            "prevalence": float(row["sum"] / row["size"]),
        }
        for hour, row in table.iterrows()
    ]


def summarize(reports):
    """Keep scopes/protocols separate; never treat overlapping runs as independent."""
    groups = {}
    for report in reports:
        key = (
            report["dataset_id"],
            report["source"]["csv_sha256"],
            report["source"]["sampling"],
            report["rows"],
            report["split"],
        )
        groups.setdefault(key, []).append(report)
    output = []
    for key, runs in sorted(groups.items()):
        seeds = [run["seed"] for run in runs]
        if len(set(seeds)) != len(seeds):
            raise ValueError("Duplicate seeds in a summary group")
        models = []
        for name in [m["name"] for m in runs[0]["models"]]:
            measurements = [next(m for m in r["models"] if m["name"] == name) for r in runs]
            statistics = {}
            for metric in (*METRICS, "false_positive_rate", "false_negative_rate"):
                values = np.asarray([m["test"][metric] for m in measurements])
                statistics[metric] = {
                    "mean": float(values.mean()),
                    "sample_std": float(values.std(ddof=1)) if len(values) > 1 else None,
                    "minimum": float(values.min()),
                    "maximum": float(values.max()),
                    "by_seed": dict(zip(map(str, seeds), values.tolist())),
                }
            models.append(
                {
                    "name": name,
                    "test": statistics,
                    "thresholds": dict(
                        zip(map(str, seeds), [m["threshold"] for m in measurements])
                    ),
                    "selected_count": sum(r["selected_model"] == name for r in runs),
                }
            )
        output.append(
            {
                "dataset_id": key[0],
                "csv_sha256": key[1],
                "sampling": key[2],
                "rows": key[3],
                "split": key[4],
                "seeds": seeds,
                "versions": [r["version"] for r in runs],
                "models": models,
            }
        )
    return {
        "report_schema_version": 1,
        "execution_status": "verified",
        "scope": "Descriptive repeated-seed sensitivity; independently fitted in-domain models",
        "uncertainty": "Sample SD/range across overlapping holdouts or a shared temporal test. "
        "Not independent dataset replications; no naive t-interval or significance claim.",
        "groups": output,
    }


def main():
    from app.benchmark_data import read_paysim
    from app.benchmarks import train

    parser = argparse.ArgumentParser(description="Sequential full-source PaySim reliability study")
    parser.add_argument("--csv", type=Path, required=True)
    parser.add_argument("--seeds", nargs="+", type=int, default=[42, 2026, 2027])
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    expected = [
        args.output_dir / f"paysim-full-{split}-seed{seed}.json"
        for split in ("stratified", "chronological")
        for seed in args.seeds
    ]
    if (any(p.exists() for p in expected) and not args.resume) or args.summary.exists():
        parser.error("Outputs already exist; refusing to repeat or overwrite completed experiments")
    if len(args.seeds) != len(set(args.seeds)):
        parser.error("Seeds must be unique")
    data, audit = read_paysim(args.csv)
    print(
        f"Prepared {len(data.x):,} rows using {audit['prepared_bytes'] / 1024**2:.1f} MiB",
        flush=True,
    )
    reports = []
    for split in ("stratified", "chronological"):
        for seed in args.seeds:
            path = args.output_dir / f"paysim-full-{split}-seed{seed}.json"
            if path.exists():
                report = json.loads(path.read_text())
                if (
                    report.get("implementation_sha256") != implementation_sha256()
                    or report["source"]["csv_sha256"] != audit["csv_sha256"]
                    or report["seed"] != seed
                    or report["split"] != split
                    or report["rows"] != len(data.x)
                ):
                    parser.error(f"Existing report does not match source/protocol: {path}")
                reports.append(report)
                print(f"Reused completed report {path}", flush=True)
                continue
            print(f"Starting {split}, seed {seed}", flush=True)
            report = train(
                data, "paysim", audit, split, seed=seed, bootstrap_repeats=200 if seed == 42 else 0
            )
            write_report(path, report)
            reports.append(report)
            print(f"Saved {path}; duration {report['duration_seconds']}s", flush=True)
    write_report(args.summary, summarize(reports))


if __name__ == "__main__":
    main()
