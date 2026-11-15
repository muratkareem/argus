import json

import numpy as np
import pytest
from app.benchmark_data import prepare
from app.benchmark_reliability import day_bootstrap, error_analysis, rank_metrics, summarize
from app.ml import metrics, partition_indices
from sklearn.metrics import (
    average_precision_score,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from test_benchmark_data import paysim_fixture


def test_tied_weighted_rank_metrics_match_sklearn():
    y = np.array([0, 1, 0, 1, 1, 0])
    scores = np.array([0.1, 0.8, 0.8, 0.1, 0.5, 0.5])
    weight = np.array([1, 0, 3, 2, 1, 4])
    order = np.argsort(-scores, kind="stable")
    start = np.r_[0, np.flatnonzero(np.diff(scores[order])) + 1]
    positive = np.add.reduceat((weight * y)[order], start)
    negative = np.add.reduceat((weight * (1 - y))[order], start)
    for threshold in (0.0, 0.1, 0.5, 0.8, 1.0):
        selected = int(np.searchsorted(-scores[order][start], -threshold, side="right"))
        actual = rank_metrics(positive, negative, selected)
        expected = {
            "precision": precision_score(
                y, scores >= threshold, sample_weight=weight, zero_division=0
            ),
            "recall": recall_score(y, scores >= threshold, sample_weight=weight),
            "f1": f1_score(y, scores >= threshold, sample_weight=weight),
            "average_precision": average_precision_score(y, scores, sample_weight=weight),
            "roc_auc": roc_auc_score(y, scores, sample_weight=weight),
        }
        for key in expected:
            if key == "precision" and threshold == 1.0:
                assert np.isnan(actual[key])
            else:
                assert actual[key] == pytest.approx(expected[key], abs=1e-12)


def test_day_bootstrap_is_deterministic_reports_invalid_replicates_and_cluster_count():
    y = np.tile([0, 1], 20)
    scores = np.tile([0.1, 0.9], 20)
    hours = np.repeat(np.arange(1, 20 * 24, 24), 2)
    first = day_bootstrap(y, scores, hours, 0.5, repeats=30)
    assert first == day_bootstrap(y, scores, hours, 0.5, repeats=30)
    assert first["clusters"] == 20
    assert first["intervals"]["average_precision"] == [1.0, 1.0]
    assert first["valid_replicates"]["recall"] == 30
    no_alerts = day_bootstrap(y, scores, hours, 1.0, repeats=30)
    assert no_alerts["intervals"]["precision"] is None
    assert no_alerts["valid_replicates"]["precision"] == 0
    with pytest.raises(ValueError, match="two observed"):
        day_bootstrap([0, 1], [0.1, 0.9], [1, 2], 0.5)
    with pytest.raises(ValueError, match="two bootstrap"):
        day_bootstrap(y, scores, hours, 0.5, repeats=1)


def test_seed_controls_random_splits_but_not_chronological_boundaries():
    data = prepare(paysim_fixture(), "paysim")
    import pandas as pd

    frame = pd.DataFrame({"Time": data.time, "Class": data.y})
    random_a = partition_indices(frame, seed=42)
    random_b = partition_indices(frame, seed=2026)
    assert not np.array_equal(random_a[0], random_b[0])
    chronological_a = partition_indices(frame, "chronological", seed=42)
    chronological_b = partition_indices(frame, "chronological", seed=2026)
    assert all(np.array_equal(a, b) for a, b in zip(chronological_a, chronological_b))


def test_error_groups_reconstruct_confusion_matrix_without_exporting_identifiers():
    data = prepare(paysim_fixture(), "paysim")
    indices = np.arange(len(data.x))
    scores = np.linspace(0, 1, len(indices))
    result = error_analysis(data, indices, scores, 0.5)
    cm = metrics(data.y, scores, 0.5)["confusion_matrix"]
    assert [sum(g[k] for g in result["by_type"]) for k in ("tn", "fp", "fn", "tp")] == list(
        np.array(cm).ravel()
    )
    assert sum(g["rows"] for g in result["error_groups"].values()) == len(indices)
    assert "nameOrig" not in json.dumps(result)


def test_summary_keeps_scope_separate_and_uses_sample_sd():
    from app.benchmarks import RESEARCH_DIR

    report = json.loads((RESEARCH_DIR / "benchmarks/paysim-stratified.json").read_text())
    second = json.loads(json.dumps(report))
    second["seed"] = 2026
    second["models"][0]["test"]["average_precision"] += 0.1
    sample = json.loads(json.dumps(report))
    sample["rows"] = 100000
    summary = summarize([report, second, sample])
    assert len(summary["groups"]) == 2
    full = next(g for g in summary["groups"] if g["rows"] == 200000)
    value = full["models"][0]["test"]["average_precision"]
    assert value["sample_std"] == pytest.approx(0.1 / np.sqrt(2))
    assert value["mean"] == pytest.approx(report["models"][0]["test"]["average_precision"] + 0.05)
    with pytest.raises(ValueError, match="Duplicate seeds"):
        summarize([report, report])


def test_report_publication_is_atomic_exclusive_and_cleans_invalid_output(tmp_path):
    from app.benchmark_reliability import write_report

    target = tmp_path / "report.json"
    write_report(target, {"measured": 1})
    with pytest.raises(FileExistsError):
        write_report(target, {"measured": 2})
    assert json.loads(target.read_text()) == {"measured": 1}
    with pytest.raises(ValueError):
        write_report(tmp_path / "invalid.json", {"metric": float("nan")})
    assert [p.name for p in tmp_path.iterdir()] == ["report.json"]
