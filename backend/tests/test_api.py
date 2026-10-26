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


def test_invalid_inputs_and_disabled_copilot(client):
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
    assert client.post("/api/v1/copilot", json={"question": "test"}).status_code == 503
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


def test_enabled_copilot_uses_only_readonly_evidence(settings, monkeypatch):
    settings.ollama_enabled = True
    requests = []

    class FakeResponse:
        def raise_for_status(self):
            pass

        def json(self):
            return {"message": {"content": "Synthetic case evidence only."}}

    class FakeClient:
        def __init__(self, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass

        async def post(self, url, json):
            requests.append(json)
            return FakeResponse()

    monkeypatch.setattr("app.main.httpx.AsyncClient", FakeClient)
    with TestClient(create_app(settings)) as client:
        cid = client.post("/api/v1/cases", json={"title": "Grounded case"}).json()["id"]
        assert client.post("/api/v1/copilot", json={"question": "Summarize"}).status_code == 422
        result = client.post("/api/v1/copilot", json={"question": "Summarize", "case_id": cid})
        assert result.status_code == 200
        assert result.json()["evidence"]["analyst_case"]["title"] == "Grounded case"
        assert "tools" not in requests[0]
        assert "Grounded case" in requests[0]["messages"][1]["content"]
