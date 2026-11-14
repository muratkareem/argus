import json

import numpy as np
import pandas as pd
import pytest
from app.ml import (
    FEATURES,
    Predictor,
    metrics,
    partition_indices,
    select_threshold,
    synthetic,
    threshold_analysis,
    train,
    validate_frame,
)


def test_training_and_inference_are_consistent_and_provenance_guarded(artifacts):
    predictor = Predictor(artifacts)
    frame = synthetic(12, seed=938)
    bundle, scores = predictor.predict(frame, "synthetic")
    loaded_again, second = Predictor(artifacts).predict(frame, "synthetic")
    np.testing.assert_array_equal(scores, second)
    assert bundle["version"] == loaded_again["version"]
    with pytest.raises(ValueError, match="cannot score"):
        predictor.predict(frame, "ulb")
    report = json.loads((artifacts / bundle["version"] / "report.json").read_text())
    assert {m["name"] for m in report["models"]} == {
        "Logistic Regression",
        "Random Forest",
        "XGBoost",
    }
    assert sum(p["rows"] for p in report["partitions"].values()) == report["rows"]
    assert report["report_schema_version"] == 2
    assert bundle["feature_schema"] == FEATURES
    assert bundle["model_name"] == report["selected_model"]
    audit = report["dataset_audit"]
    assert audit["feature_schema"] == FEATURES
    assert sum(audit["class_counts"].values()) == report["rows"]
    assert audit["fraud_fraction"] == report["fraud_rows"] / report["rows"]
    assert not any(audit["missing_values"].values())
    assert audit["amount"]["count"] == report["rows"]
    expected = max(report["models"], key=lambda m: m["validation_average_precision"])["name"]
    assert report["selected_model"] == expected
    for model in report["models"]:
        assert 0 <= model["threshold"] <= 1
        assert (
            sum(map(sum, model["test"]["confusion_matrix"])) == report["partitions"]["test"]["rows"]
        )
        timing = model["inference_latency"]
        assert timing["single_p95_ms"] >= timing["single_p50_ms"] > 0
        assert timing["batch_1000_p95_ms"] >= timing["batch_1000_ms"] > 0
        assert timing["single_repeats"] == 20
        assert timing["batch_repeats"] == 5


def test_shap_explains_actual_model(artifacts):
    result = Predictor(artifacts).explain(
        synthetic(1, seed=984)[FEATURES].iloc[0].to_dict(), "synthetic"
    )
    assert len(result["features"]) == 30
    raw = result["base_value"] + sum(f["contribution"] for f in result["features"])
    # Linear and XGBoost raw SHAP output is a logit; forest output is probability.
    candidates = [raw, 1 / (1 + np.exp(-raw))]
    assert min(abs(s - result["risk_score"]) for s in candidates) < 1e-5
    assert result["additivity_error"] < 1e-5
    assert result["output_space"] in {"log-odds", "probability"}


def test_shap_cache_is_bounded_and_returns_independent_results(artifacts):
    predictor = Predictor(artifacts)
    features = synthetic(1, seed=984)[FEATURES].iloc[0].to_dict()
    first = predictor.explain(features, "synthetic")
    assert first["cache_hit"] is False
    explainer = predictor._explainer
    first["features"][0]["contribution"] = 999
    second = predictor.explain(features, "synthetic")
    assert second["cache_hit"] is True
    assert predictor._explainer is explainer
    assert second["features"][0]["contribution"] != 999
    for i in range(130):
        row = dict(features, Amount=float(i))
        predictor.explain(row, "synthetic")
    assert len(predictor._explanations) == 128
    assert predictor._explainer is explainer


def test_validation_rejects_malformed_data():
    with pytest.raises(ValueError, match="Missing columns"):
        validate_frame(pd.DataFrame({"Amount": [1]}))
    df = synthetic(100)
    df.loc[0, "V1"] = np.nan
    with pytest.raises(ValueError, match="non-finite"):
        validate_frame(df)


def test_schema_is_canonical_and_rejects_ambiguous_columns():
    frame = synthetic(100)
    canonical = validate_frame(frame)
    reordered = validate_frame(frame[frame.columns[::-1]])
    pd.testing.assert_frame_equal(canonical, reordered)
    with pytest.raises(ValueError, match="Duplicate column"):
        validate_frame(pd.concat([frame, frame[["Amount"]]], axis=1))


@pytest.mark.parametrize("split", ["stratified", "chronological"])
def test_partitions_are_disjoint_reproducible_and_preserve_timestamps(split):
    frame = synthetic(1000)
    frame["Time"] = (frame.Time // 1000) * 1000
    first = partition_indices(frame, split)
    second = partition_indices(frame, split)
    assert sorted(np.concatenate(first)) == list(range(len(frame)))
    for left, right in zip(first, second):
        np.testing.assert_array_equal(left, right)
    if split == "chronological":
        assert frame.Time.iloc[first[0]].max() < frame.Time.iloc[first[1]].min()
        assert frame.Time.iloc[first[1]].max() < frame.Time.iloc[first[2]].min()
    with pytest.raises(ValueError, match="split must"):
        partition_indices(frame, "unsupported")


def test_predictor_validates_schema_before_inference(artifacts):
    frame = synthetic(2)
    frame.loc[0, "Amount"] = -1
    with pytest.raises(ValueError, match="nonnegative"):
        Predictor(artifacts).predict(frame, "synthetic")
    df = synthetic(100)
    df.loc[0, "Class"] = 2
    with pytest.raises(ValueError, match="binary"):
        validate_frame(df)


def test_artifact_manifest_is_integrity_checked_and_model_is_loaded_once(artifacts, tmp_path, monkeypatch):
    import shutil

    import joblib

    shutil.copytree(artifacts, tmp_path / "artifacts")
    directory = tmp_path / "artifacts"
    manifest = json.loads((directory / "current.json").read_text())
    assert len(manifest["model_sha256"]) == 64
    original = joblib.load
    calls = []

    def counting_load(path):
        calls.append(path)
        return original(path)

    monkeypatch.setattr(joblib, "load", counting_load)
    predictor = Predictor(directory)
    predictor.load()
    predictor.load()
    assert len(calls) == 1
    model_path = directory / manifest["version"] / "model.joblib"
    with model_path.open("ab") as model_file:
        model_file.write(b"corrupt")
    with pytest.raises(ValueError, match="checksum"):
        Predictor(directory).load()
    assert len(calls) == 1  # Reject changed bytes before unpickling.


@pytest.mark.parametrize("manifest", [{"version": "../outside"}, {"version": None}, {}, {"version": 123}])
def test_artifact_manifest_rejects_unsafe_or_invalid_versions(tmp_path, manifest):
    (tmp_path / "current.json").write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match="artifact"):
        Predictor(tmp_path).load()


def test_duplicate_removal_and_chronological_split(tmp_path):
    df = synthetic(500)
    df = pd.concat([df, df.iloc[:8]])
    report = train(df, tmp_path, "synthetic", split="chronological")
    assert report["duplicates_removed"] == 8
    assert report["split"] == "chronological"
    assert sum(v["rows"] for v in report["partitions"].values()) == 500
    conflicting = synthetic(150)
    copy = conflicting.iloc[[0]].copy()
    copy["Class"] = 1 - copy["Class"]
    with pytest.raises(ValueError, match="conflicting"):
        train(pd.concat([conflicting, copy]), tmp_path, "synthetic")


def test_metrics_do_not_reward_majority_accuracy():
    result = metrics([0] * 99 + [1], np.array([0.01] * 100), 0.5)
    assert result["recall"] == 0
    assert result["f1"] == 0
    assert result["confusion_matrix"] == [[99, 0], [1, 0]]
    assert result["false_negative_rate"] == 1
    assert result["false_positive_rate"] == 0
    assert result["brier_score"] == pytest.approx((99 * 0.01**2 + 0.99**2) / 100)
    assert result["roc_curve"][0] == {"false_positive_rate": 0, "true_positive_rate": 0}
    assert result["roc_curve"][-1] == {"false_positive_rate": 1, "true_positive_rate": 1}
    assert result["calibration_curve"] == [
        {"mean_predicted_probability": pytest.approx(0.01), "fraction_positive": 0.01}
    ]


@pytest.mark.parametrize("threshold", [-0.1, 1.1, np.nan])
def test_metrics_reject_invalid_threshold(threshold):
    with pytest.raises(ValueError, match="threshold"):
        metrics([0, 1], np.array([0.2, 0.8]), threshold)


@pytest.mark.parametrize("scores", [[-1, 0.5], [0.2, 2], [0.2, np.nan], [[0.2], [0.8]]])
def test_metrics_reject_invalid_scores(scores):
    with pytest.raises(ValueError, match="Scores"):
        metrics([0, 1], scores, 0.5)


def test_threshold_selection_and_cost_tradeoff_use_validation_scores():
    labels, scores = [0, 0, 1, 1], np.array([0.1, 0.7, 0.6, 0.9])
    selected = select_threshold(labels, scores)
    assert selected == 0.6
    analysis = threshold_analysis(labels, scores, selected, 2, 10)
    assert analysis["partition"] == "validation"
    chosen = next(p for p in analysis["points"] if p["threshold"] == selected)
    assert chosen["false_positives"] == 1
    assert chosen["false_negatives"] == 0
    assert chosen["estimated_cost"] == 2
    assert analysis["points"][0]["recall"] == 1
    assert analysis["points"][-1]["recall"] == 0
    assert all(
        left["false_positives"] >= right["false_positives"]
        and left["false_negatives"] <= right["false_negatives"]
        for left, right in zip(analysis["points"], analysis["points"][1:])
    )
    with pytest.raises(ValueError, match="costs"):
        threshold_analysis(labels, scores, selected, false_negative_cost=-1)


@pytest.mark.parametrize("kind", ["linear", "forest", "xgboost"])
def test_explanation_supports_every_candidate_algorithm(tmp_path, kind):
    import joblib
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler
    from xgboost import XGBClassifier

    frame = synthetic(250, seed=771)
    candidates = {
        "linear": make_pipeline(StandardScaler(), LogisticRegression(max_iter=500)),
        "forest": RandomForestClassifier(n_estimators=20, max_depth=4, random_state=42),
        "xgboost": XGBClassifier(n_estimators=20, max_depth=3, random_state=42, n_jobs=2),
    }
    model = candidates[kind].fit(frame[FEATURES], frame.Class)
    version = "abcdef"
    (tmp_path / version).mkdir()
    joblib.dump(
        {
            "model": model,
            "background": frame[FEATURES].iloc[:50],
            "threshold": 0.5,
            "version": version,
            "provenance": "synthetic",
        },
        tmp_path / version / "model.joblib",
    )
    (tmp_path / "current.json").write_text(json.dumps({"version": version}))
    result = Predictor(tmp_path).explain(frame[FEATURES].iloc[0].to_dict(), "synthetic")
    raw = result["base_value"] + sum(f["contribution"] for f in result["features"])
    reconstructed = raw if kind == "forest" else 1 / (1 + np.exp(-raw))
    assert reconstructed == pytest.approx(result["risk_score"], abs=1e-5)


def test_saved_pr_curve_preserves_endpoints_and_recall_changes():
    # Thousands of low-score negatives must not consume all sampled curve points.
    y = np.array([0] * 3000 + [1] * 20)
    scores = np.r_[np.linspace(0, 0.2, 3000), np.linspace(0.4, 0.99, 20)]
    curve = metrics(y, scores, 0.5)["pr_curve"]
    assert curve[0]["recall"] == 1
    assert curve[-1] == {"recall": 0.0, "precision": 1.0}
    assert any(p["recall"] < 0.5 and p["precision"] == 1 for p in curve)
    assert len(curve) <= 400
