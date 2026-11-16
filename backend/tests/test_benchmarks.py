import json

import numpy as np
import pandas as pd
import pytest
from app import benchmarks
from app.benchmark_data import prepare
from app.ml import partition_indices
from test_benchmark_data import paysim_fixture


def test_confidence_intervals_handle_zero_denominator_and_boundaries():
    assert benchmarks.wilson(0, 0) is None
    lower, upper = benchmarks.wilson(8, 10)
    assert lower == pytest.approx(0.49016, abs=0.0001)
    assert upper == pytest.approx(0.94332, abs=0.0001)
    assert benchmarks.wilson(0, 20)[0] == 0
    assert benchmarks.wilson(20, 20)[1] <= 1


def test_chronological_partitions_keep_hours_together_and_signatures_disjoint():
    data = prepare(paysim_fixture(), "paysim")
    idx = partition_indices(pd.DataFrame({"Time": data.time, "Class": data.y}), "chronological")
    for left, right in zip(idx, idx[1:]):
        assert data.time.iloc[left].max() < data.time.iloc[right].min()
        assert not set(data.fingerprints.iloc[left]) & set(data.fingerprints.iloc[right])
    assert sum(map(len, idx)) == len(data.x)


def test_test_labels_do_not_change_validation_selection_or_thresholds(monkeypatch):
    original_candidates = benchmarks.candidates

    def small_candidates(ratio, seed=42):
        candidates = original_candidates(ratio, seed=seed)
        for estimators in candidates.values():
            for estimator in estimators:
                if "n_estimators" in estimator.get_params():
                    estimator.set_params(n_estimators=5)
        return candidates

    monkeypatch.setattr(benchmarks, "candidates", small_candidates)
    frame = paysim_fixture()
    first = benchmarks.train(frame, "paysim", {"fixture": True})
    frame.loc[frame.step >= 32, "isFraud"] = 1 - frame.loc[frame.step >= 32, "isFraud"]
    second = benchmarks.train(frame, "paysim", {"fixture": True})
    for name in first["candidate_search"]:
        for left, right in zip(first["candidate_search"][name], second["candidate_search"][name]):
            assert left["parameters"] == right["parameters"]
            assert left["validation_average_precision"] == pytest.approx(
                right["validation_average_precision"], abs=1e-12
            )
    for left, right in zip(first["models"], second["models"]):
        assert left["threshold"] == pytest.approx(right["threshold"], abs=1e-12)
        for metric in ("precision", "recall", "f1", "average_precision", "roc_auc", "brier_score"):
            assert left["validation"][metric] == pytest.approx(
                right["validation"][metric], abs=1e-12
            )
        assert left["validation"]["confusion_matrix"] == right["validation"]["confusion_matrix"]
        assert (
            left["test"]["recall"] != right["test"]["recall"]
            or left["test"]["average_precision"] != right["test"]["average_precision"]
        )
    assert (
        first["partitions"]["train"]["time_maximum"] < first["partitions"]["test"]["time_minimum"]
    )
    assert first["preprocessing"]["fit_partition"] == "train only"
    assert np.isfinite(first["models"][0]["inference_latency"]["single_p95_ms"])
    json.dumps(first, allow_nan=False)


def test_catalog_publishes_real_reports_without_altering_ulb_artifacts():
    payload = benchmarks.catalog()
    assert {d["id"] for d in payload["datasets"]} == {"ulb", "ieee_cis", "paysim"}
    ulb = [r for r in payload["experiments"] if r["dataset_id"] == "ulb"]
    assert len(ulb) == 2
    assert {r["split"] for r in ulb} == {"stratified", "chronological"}
    assert not payload["report_errors"]
    assert all(r["data_kind"] == "real" for r in ulb)
    assert all("confidence_intervals" in m["test"] for r in ulb for m in r["models"])


def test_catalog_rejects_incomplete_or_invalid_reports(tmp_path):
    directory = tmp_path / "benchmarks"
    directory.mkdir()
    (directory / "fake.json").write_text(
        json.dumps({"dataset_id": "paysim", "execution_status": "pending"})
    )
    payload = benchmarks.catalog(tmp_path)
    assert payload["experiments"] == []
    assert len(payload["report_errors"]) == 1
    assert (
        next(d for d in payload["datasets"] if d["id"] == "ieee_cis")["status"] == "access_required"
    )


def test_benchmark_api_is_independent_of_active_model_and_preserves_contract(client):
    before = client.get("/api/v1/models").json()
    response = client.get("/api/v1/benchmarks")
    assert response.status_code == 200
    payload = response.json()
    assert len(payload["datasets"]) == 3 and not payload["report_errors"]
    assert any(r["dataset_id"] == "ulb" for r in payload["experiments"])
    assert client.get("/api/v1/models").json() == before
    assert set(before) == {"active_version", "experiments"}


@pytest.mark.parametrize("corruption", ["selected", "counts", "shape", "nan"])
def test_corrupt_report_is_excluded_without_hiding_valid_evidence(tmp_path, corruption):
    report = json.loads((benchmarks.RESEARCH_DIR / "benchmarks/paysim-stratified.json").read_text())
    if corruption == "selected":
        report["selected_model"] = "Missing model"
    elif corruption == "counts":
        report["models"][0]["test"]["confusion_matrix"][0][0] = -1
    elif corruption == "shape":
        report["models"][0]["test"]["confusion_matrix"] = [[40000]]
    else:
        report["models"][0]["test"]["roc_auc"] = float("nan")
    directory = tmp_path / "benchmarks"
    directory.mkdir()
    (directory / "broken.json").write_text(json.dumps(report))
    payload = benchmarks.catalog(tmp_path)
    assert not payload["experiments"] and len(payload["report_errors"]) == 1


def test_ieee_training_executes_all_algorithms_on_explicit_unit_fixture(monkeypatch):
    original = benchmarks.candidates

    def tiny(ratio, seed=42):
        choices = original(ratio, seed=seed)
        for estimators in choices.values():
            for estimator in estimators:
                if "n_estimators" in estimator.get_params():
                    estimator.set_params(n_estimators=3)
        return choices

    monkeypatch.setattr(benchmarks, "candidates", tiny)
    frame = pd.DataFrame(
        {
            "TransactionID": np.arange(120),
            "TransactionDT": np.arange(120),
            "TransactionAmt": np.arange(120) + 1.0,
            "ProductCD": ["W", "C"] * 60,
            "isFraud": (np.arange(120) % 3 == 0).astype(int),
            "V1": np.where(np.arange(120) % 4, 1.0, np.nan),
        }
    )
    report = benchmarks.train(frame, "ieee_cis", {"fixture": True})
    assert len(report["models"]) == 3 and report["dataset_id"] == "ieee_cis"
    assert report["source"]["fixture"] is True
    assert report["temporal_audit"] is None  # IEEE TransactionDT is seconds, not PaySim hours.
    assert "TransactionDT" in report["preprocessing"]["excluded"]
    assert all(np.isfinite(m["test"]["average_precision"]) for m in report["models"])
