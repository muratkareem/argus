import io

import pandas as pd
import pytest
from app.main import create_app
from app.ml import FEATURES, synthetic
from fastapi.testclient import TestClient


def test_ingest_score_filter_export_and_overview(client, imported, csv_content):
    assert imported["imported"] == 80
    repeated = client.post(
        "/api/v1/datasets/upload",
        files={"file": ("same.csv", csv_content)},
        data={"provenance": "synthetic"},
    ).json()
    assert repeated["imported"] == 0
    assert repeated["duplicates"] == 80
    stats = client.get("/api/v1/overview").json()
    assert stats["total"] == 80
    assert stats["scored"] == 80
    assert sum(b["count"] for b in stats["risk_distribution"]) == 80
    assert sum(t["count"] for t in stats["trend"]) == 80
    page = client.get("/api/v1/transactions?page_size=7&sort=amount&direction=asc").json()
    assert page["total"] == 80 and len(page["items"]) == 7
    assert page["items"] == sorted(page["items"], key=lambda t: t["amount"])
    flagged = client.get("/api/v1/transactions?flagged=true").json()
    assert flagged["total"] == stats["flagged"]
    assert all(t["flagged"] for t in flagged["items"])
    tx = client.get(f"/api/v1/transactions/{page['items'][0]['id']}").json()
    prediction = client.post(
        "/api/v1/predict", json={"features": tx["features"], "provenance": "synthetic"}
    ).json()
    assert prediction["risk_score"] == pytest.approx(tx["risk_score"], abs=1e-12)
    assert prediction["model_version"] == tx["model_version"]
    explanation = client.get(f"/api/v1/transactions/{tx['id']}/explanation")
    assert explanation.status_code == 200, explanation.text
    assert explanation.json()["matches_stored_prediction"]
    assert client.post(f"/api/v1/datasets/{imported['dataset_id']}/score").json()["scored"] == 80
    exported = pd.read_csv(io.StringIO(client.get("/api/v1/transactions/export").text))
    assert len(exported) == 80
    assert len(client.get("/api/v1/transactions/export?format=json").json()["transactions"]) == 80
    assert len(client.get("/api/v1/models").json()["experiments"]) >= 1


def test_investigation_persists_across_app_restart(client, settings, imported):
    txid = client.get("/api/v1/transactions").json()["items"][0]["id"]
    case = client.post(
        "/api/v1/cases",
        json={
            "title": "Review high risk transaction",
            "transaction_ids": [txid, txid],
            "priority": "High",
        },
    )
    assert case.status_code == 201
    cid = case.json()["id"]
    assert case.json()["transaction_ids"] == [txid]
    assert (
        client.post(
            f"/api/v1/cases/{cid}/notes",
            json={"body": "Verify anonymized features; synthetic record"},
        ).status_code
        == 201
    )
    assert (
        client.patch(
            f"/api/v1/cases/{cid}",
            json={"status": "In Review", "decision": "Pending analyst verification"},
        ).status_code
        == 200
    )
    assert (
        client.post(f"/api/v1/cases/{cid}/transactions", json={"transaction_id": txid}).status_code
        == 200
    )
    with TestClient(create_app(settings)) as restarted:
        saved = restarted.get(f"/api/v1/cases/{cid}").json()
        assert saved["status"] == "In Review"
        assert saved["decision"] == "Pending analyst verification"
        assert len(saved["notes"]) == 1
        assert restarted.get("/api/v1/cases?q=anonymized").json()[0]["id"] == cid
        report = restarted.get(f"/api/v1/cases/{cid}/export").json()
        assert report["transactions"][0]["model_version"]
        assert report["transactions"][0]["provenance"] == "synthetic"


def test_invalid_inputs_and_removed_generation_routes(client):
    assert (
        client.post("/api/v1/predict", json={"features": {}, "provenance": "synthetic"}).status_code
        == 422
    )
    assert client.get("/api/v1/transactions?sort=__dict__").status_code == 422
    assert client.get("/api/v1/transactions?page=0").status_code == 422
    assert (
        client.post(
            "/api/v1/datasets/upload",
            files={"file": ("x.csv", b"x\n1")},
            data={"provenance": "ulb"},
        ).status_code
        == 422
    )
    assert client.get("/api/v1/transactions/999999").status_code == 404
    assert client.post("/api/v1/copilot", json={"question": "test"}).status_code == 404
    assert (
        client.post(
            "/api/v1/cases", json={"title": "Invalid case", "transaction_ids": [999999]}
        ).status_code
        == 404
    )
    assert client.patch("/api/v1/cases/1", json={"status": "unknown"}).status_code == 422


def test_ulb_import_never_uses_synthetic_model(client):
    frame = synthetic(10, seed=551).drop(columns=["Class"])
    result = client.post(
        "/api/v1/datasets/upload",
        files={"file": ("ulb-shaped.csv", frame.to_csv(index=False).encode())},
        data={"provenance": "ulb"},
    )
    assert result.status_code == 200
    rows = client.get("/api/v1/transactions?provenance=ulb").json()["items"]
    assert all(r["risk_score"] is None for r in rows)
    assert client.post(f"/api/v1/datasets/{result.json()['dataset_id']}/score").status_code == 409
    features = frame[FEATURES].iloc[0].to_dict()
    assert (
        client.post("/api/v1/predict", json={"features": features, "provenance": "ulb"}).status_code
        == 409
    )


def test_no_model_and_upload_limit(settings, tmp_path):
    settings.artifact_dir = tmp_path / "missing"
    settings.max_upload_bytes = 15
    with TestClient(create_app(settings)) as client:
        assert (
            client.post(
                "/api/v1/predict",
                json={
                    "features": synthetic(1)[FEATURES].iloc[0].to_dict(),
                    "provenance": "synthetic",
                },
            ).status_code
            == 503
        )
        assert (
            client.post(
                "/api/v1/datasets/upload",
                files={"file": ("x.csv", b"x" * 16)},
                data={"provenance": "synthetic"},
            ).status_code
            == 413
        )
        assert client.get("/api/v1/models").json()["experiments"] == []


def test_graph_has_separate_synthetic_relationships(client):
    from app.data import seed_graph

    with client.app.state.session_factory() as session:
        seed_graph(session)
    graph = client.get("/api/v1/graph").json()
    assert graph["provenance"] == "synthetic"
    assert {n["data"]["kind"] for n in graph["nodes"]} == {
        "Account",
        "Card",
        "Device",
        "Merchant",
        "Transaction",
    }
    node_ids = {n["data"]["id"] for n in graph["nodes"]}
    assert all(
        e["data"]["source"] in node_ids and e["data"]["target"] in node_ids for e in graph["edges"]
    )


def test_generation_routes_absent_from_schema(client):
    routes = client.get("/openapi.json").json()["paths"]
    assert not any("copilot" in route for route in routes)
    assert "ollama_enabled" not in client.get("/api/v1/settings").json()


@pytest.mark.parametrize("threshold, expected", [(0, 1), (1, 0)])
def test_request_threshold_does_not_change_probability(client, threshold, expected):
    features = synthetic(1, seed=827)[FEATURES].iloc[0].to_dict()
    data = {
        "features": features,
        "provenance": "synthetic",
        "threshold": threshold,
        "transaction_id": "demo-1",
    }
    result = client.post("/api/v1/predict", json=data)
    assert result.status_code == 200, result.text
    output = result.json()
    assert output["predicted_class"] == expected
    assert output["decision_threshold"] == threshold
    assert output["transaction_id"] == "demo-1"
    assert 0 <= output["fraud_probability"] <= 1
    data.pop("threshold")
    assert (
        client.post("/api/v1/predict", json=data).json()["fraud_probability"]
        == output["fraud_probability"]
    )


@pytest.mark.parametrize("threshold", [-0.1, 1.1])
def test_invalid_threshold_rejected(client, threshold):
    data = {
        "features": synthetic(1)[FEATURES].iloc[0].to_dict(),
        "provenance": "synthetic",
        "threshold": threshold,
    }
    assert client.post("/api/v1/predict", json=data).status_code == 422


def test_inference_rejects_label_leakage(client):
    features = synthetic(1).iloc[0].to_dict()
    assert (
        client.post(
            "/api/v1/predict", json={"features": features, "provenance": "synthetic"}
        ).status_code
        == 422
    )


def test_batch_prediction_is_vectorized_and_matches_single(client, monkeypatch):
    records = synthetic(7, seed=772)[FEATURES].to_dict("records")
    predictor = client.app.state.predictor
    original = predictor.predict
    calls = []

    def counted(frame, provenance):
        calls.append(len(frame))
        return original(frame, provenance)

    monkeypatch.setattr(predictor, "predict", counted)
    result = client.post(
        "/api/v1/predict/batch",
        json={
            "transactions": [
                {"id": str(i), "features": features} for i, features in enumerate(records)
            ],
            "provenance": "synthetic",
            "threshold": 0.4,
        },
    )
    assert result.status_code == 200, result.text
    assert calls == [7]
    body = result.json()
    assert body["count"] == 7
    for i, item in enumerate(body["items"]):
        single = client.post(
            "/api/v1/predict",
            json={"features": records[i], "provenance": "synthetic", "threshold": 0.4},
        ).json()
        assert item["transaction_id"] == str(i)
        assert item["fraud_probability"] == pytest.approx(single["fraud_probability"], abs=1e-12)
        assert item["predicted_class"] == single["predicted_class"]


@pytest.mark.parametrize("size", [0, 1001])
def test_batch_size_limits(client, size):
    item = {"features": synthetic(1)[FEATURES].iloc[0].to_dict()}
    assert (
        client.post(
            "/api/v1/predict/batch", json={"transactions": [item] * size, "provenance": "synthetic"}
        ).status_code
        == 422
    )


def test_batch_rejects_invalid_feature_and_provenance(client):
    features = synthetic(1)[FEATURES].iloc[0].to_dict()
    data = {"transactions": [{"features": features}], "provenance": "ulb"}
    assert client.post("/api/v1/predict/batch", json=data).status_code == 409
    features["Amount"] = -1
    data["provenance"] = "synthetic"
    assert client.post("/api/v1/predict/batch", json=data).status_code == 422


def test_direct_explanation_matches_requested_prediction(client):
    data = {
        "features": synthetic(1, seed=321)[FEATURES].iloc[0].to_dict(),
        "provenance": "synthetic",
    }
    prediction = client.post("/api/v1/predict", json=data).json()
    result = client.post("/api/v1/predict/explanation", json=data)
    assert result.status_code == 200, result.text
    explanation = result.json()
    assert explanation["model_version"] == prediction["model_version"]
    assert explanation["risk_score"] == pytest.approx(prediction["risk_score"])
    assert len(explanation["features"]) == 30
    assert any(f["contribution"] > 0 for f in explanation["features"])
    assert any(f["contribution"] < 0 for f in explanation["features"])
    assert "output_space" in explanation
    assert (
        client.post("/api/v1/predict/explanation", json={**data, "provenance": "ulb"}).status_code
        == 409
    )


def test_optional_api_key_and_cors(settings):
    settings.api_key = "test-key-for-local-tests-only"
    with TestClient(create_app(settings)) as client:
        assert client.get("/api/v1/health").status_code == 200
        assert client.get("/api/v1/overview").status_code == 401
        assert (
            client.get("/api/v1/overview", headers={"Authorization": "Bearer wrong"}).status_code
            == 401
        )
        good = {"Authorization": "Bearer test-key-for-local-tests-only"}
        assert client.get("/api/v1/overview", headers=good).status_code == 200
        preflight = client.options(
            "/api/v1/predict",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Authorization",
            },
        )
        assert preflight.status_code == 200
        assert preflight.headers["access-control-allow-origin"] == "http://localhost:5173"
        foreign = client.options(
            "/api/v1/predict",
            headers={
                "Origin": "https://untrusted.example",
                "Access-Control-Request-Method": "POST",
            },
        )
        assert foreign.status_code == 400


def test_nonfinite_request_has_safe_validation_error(client):
    import json

    features = synthetic(1)[FEATURES].iloc[0].to_dict()
    features["V1"] = float("nan")
    result = client.post(
        "/api/v1/predict",
        content=json.dumps({"features": features, "provenance": "synthetic"}),
        headers={"Content-Type": "application/json"},
    )
    assert result.status_code == 422
    assert "input" not in result.text
    assert result.headers["x-content-type-options"] == "nosniff"
    assert result.headers["x-request-id"]


def test_dataset_scoring_uses_bounded_chunks(client):
    frame = synthetic(4100, seed=915)
    imported = client.post(
        "/api/v1/datasets/upload",
        files={"file": ("chunks.csv", frame.to_csv(index=False).encode())},
        data={"provenance": "synthetic"},
    ).json()
    predictor = client.app.state.predictor
    original = predictor.predict
    calls = []

    def counted(frame, provenance):
        calls.append(len(frame))
        return original(frame, provenance)

    predictor.predict = counted
    result = client.post(f"/api/v1/datasets/{imported['dataset_id']}/score")
    assert result.status_code == 200, result.text
    assert result.json()["scored"] == 4100
    assert calls == [2000, 2000, 100]


def test_model_readiness_and_system_information(client, settings, tmp_path):
    assert client.get("/api/v1/ready").status_code == 200
    info = client.get("/api/v1/settings").json()
    assert info["active_model"]["status"] == "ready"
    assert info["feature_schema"] == FEATURES
    assert info["max_batch_size"] == 1000
    settings.artifact_dir = tmp_path / "empty"
    with TestClient(create_app(settings)) as empty:
        assert empty.get("/api/v1/health").status_code == 200
        assert empty.get("/api/v1/health").json()["model_status"] == "unavailable"
        assert empty.get("/api/v1/ready").status_code == 503


def test_overview_observed_labels_are_separate_from_flags(client, imported, csv_content):
    frame = pd.read_csv(io.BytesIO(csv_content))
    overview = client.get("/api/v1/overview").json()
    assert overview["labeled_fraud"] == int(frame.Class.sum())
    assert overview["labeled_legitimate"] == int((frame.Class == 0).sum())
    assert overview["unlabeled"] == 0
    assert overview["labeled_fraud"] + overview["labeled_legitimate"] == overview["total"]
