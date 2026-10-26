import json

import numpy as np
import pandas as pd
import pytest
from app.ml import FEATURES, Predictor, metrics, synthetic, train, validate_frame


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
    expected = max(report["models"], key=lambda m: m["validation_average_precision"])["name"]
    assert report["selected_model"] == expected
    for model in report["models"]:
        assert 0 <= model["threshold"] <= 1
        assert (
            sum(map(sum, model["test"]["confusion_matrix"])) == report["partitions"]["test"]["rows"]
        )


def test_shap_explains_actual_model(artifacts):
    result = Predictor(artifacts).explain(
        synthetic(1, seed=984)[FEATURES].iloc[0].to_dict(), "synthetic"
    )
    assert len(result["features"]) == 30
    raw = result["base_value"] + sum(f["contribution"] for f in result["features"])
    # Linear and XGBoost raw SHAP output is a logit; forest output is probability.
    candidates = [raw, 1 / (1 + np.exp(-raw))]
    assert min(abs(s - result["risk_score"]) for s in candidates) < 1e-5


def test_validation_rejects_malformed_data():
    with pytest.raises(ValueError, match="Missing columns"):
        validate_frame(pd.DataFrame({"Amount": [1]}))
    df = synthetic(100)
    df.loc[0, "V1"] = np.nan
    with pytest.raises(ValueError, match="non-finite"):
        validate_frame(df)
    df = synthetic(100)
    df.loc[0, "Class"] = 2
    with pytest.raises(ValueError, match="binary"):
        validate_frame(df)


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
