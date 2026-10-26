from app.data import seed_graph
from app.main import create_app
from fastapi.testclient import TestClient


def test_advanced_filters_and_export_are_consistent(client, imported):
    query = "min_amount=20&max_amount=150&min_risk=0&max_risk=1&label=0&min_time=0&max_time=172800"
    rows = client.get("/api/v1/transactions?" + query).json()
    assert rows["total"] > 0
    assert all(20 <= t["amount"] <= 150 and t["label"] == 0 for t in rows["items"])
    exported = client.get("/api/v1/transactions/export?format=json&" + query).json()
    assert len(exported["transactions"]) == rows["total"]
    assert client.get("/api/v1/transactions?min_amount=10&max_amount=1").status_code == 422
    assert client.get("/api/v1/transactions?label=3").status_code == 422
    assert client.get("/api/v1/transactions?max_risk=2").status_code == 422


def test_saved_views_persist_and_validate(client, settings):
    saved = client.post(
        "/api/v1/views",
        json={
            "name": "High value alerts",
            "filters": {"provenance": "ulb", "flagged": True, "min_amount": 500, "min_risk": 0.9},
        },
    )
    assert saved.status_code == 201, saved.text
    with TestClient(create_app(settings)) as other:
        view = other.get("/api/v1/views").json()[0]
        assert view["filters"]["min_amount"] == 500
        assert other.delete(f"/api/v1/views/{view['id']}").status_code == 200
        assert other.get("/api/v1/views").json() == []
    assert (
        client.post(
            "/api/v1/views", json={"name": "Bad", "filters": {"sort": "password"}}
        ).status_code
        == 422
    )
    assert (
        client.post(
            "/api/v1/views", json={"name": "Bad", "filters": {"min_amount": 4, "max_amount": 1}}
        ).status_code
        == 422
    )


def test_global_search_and_graph_neighborhood_use_only_real_records(client, imported):
    with client.app.state.session_factory() as session:
        seed_graph(session)
    tx = client.get("/api/v1/transactions").json()["items"][0]
    results = client.get(f"/api/v1/search?q=TX-{tx['id']:06d}").json()["results"]
    assert any(r["kind"] == "Transaction" and r["id"] == str(tx["id"]) for r in results)
    graph = client.get("/api/v1/intelligence/graph?root=device-1&depth=1").json()
    assert len(graph["nodes"]) == 4
    assert any(n["data"]["shared_accounts"] == 3 for n in graph["nodes"])
    assert len(client.get("/api/v1/intelligence/graph?root=device-1&depth=0").json()["nodes"]) == 1
    assert len(client.get("/api/v1/intelligence/graph?shared_only=true").json()["nodes"]) == 4
    assert client.get("/api/v1/intelligence/graph?root=missing").status_code == 404
    assert client.get("/api/v1/intelligence/graph?depth=9").status_code == 422


def test_timeline_and_synthetic_entity_links_are_persistent_and_idempotent(
    client, imported, settings
):
    with client.app.state.session_factory() as session:
        seed_graph(session)
    tx = client.get("/api/v1/transactions").json()["items"][0]
    case = client.post(
        "/api/v1/cases",
        json={
            "title": "Shared device review",
            "transaction_ids": [tx["id"]],
            "entity_ids": ["device-1"],
        },
    ).json()
    cid = case["id"]
    assert case["entity_ids"] == ["device-1"]
    for _ in range(2):
        assert (
            client.post(
                f"/api/v1/cases/{cid}/entities", json={"entity_id": "account-1"}
            ).status_code
            == 200
        )
    client.patch(
        f"/api/v1/cases/{cid}",
        json={
            "status": "Escalated",
            "priority": "Critical",
            "decision": "Synthetic structural cue only.",
        },
    )
    client.post(f"/api/v1/cases/{cid}/notes", json={"body": "Do not infer ULB relationships."})
    with TestClient(create_app(settings)) as other:
        events = other.get(f"/api/v1/cases/{cid}/timeline").json()
        assert len([e for e in events if e["kind"] == "entity_linked"]) == 1
        assert {"created", "status_changed", "priority_changed", "decision_changed", "note"} <= {
            e["kind"] for e in events
        }
        assert cid in other.get("/api/v1/entities/device-1").json()["case_ids"]
        report = other.get(f"/api/v1/cases/{cid}/export").json()
        assert len(report["entities"]) == 2
        assert all(e["provenance"] == "synthetic" for e in report["entities"])
        assert report["timeline"]


def test_copilot_context_is_available_without_llm_and_bounded(client, imported):
    tx = client.get("/api/v1/transactions").json()["items"][0]
    case = client.post(
        "/api/v1/cases", json={"title": "Evidence context", "transaction_ids": [tx["id"]]}
    ).json()
    for _ in range(6):
        client.post(f"/api/v1/cases/{case['id']}/notes", json={"body": "a" * 1200})
    result = client.get(f"/api/v1/copilot/context?case_id={case['id']}&transaction_id={tx['id']}")
    assert result.status_code == 200, result.text
    data = result.json()
    assert data["scope"]["case_id"] == case["id"]
    assert len(data["evidence"]["analyst_case"]["notes"]) == 4
    assert data["evidence"]["analyst_case"]["notes_total"] == 6
    assert all(len(n["body"]) <= 800 for n in data["evidence"]["analyst_case"]["notes"])
    assert any(s["id"] == f"transaction:{tx['id']}" for s in data["sources"])
    assert data["evidence"]["model_explanation"]["matches_stored_prediction"]
    assert client.get("/api/v1/copilot/context").status_code == 422
    assert client.get("/api/v1/copilot/context?case_id=999999").status_code == 404


def test_structured_copilot_rejects_unknown_citations():
    import json

    import pytest
    from app.copilot import render_interpretation
    from fastapi import HTTPException

    sections = {
        "recorded_facts": "Recorded transaction.",
        "model_output": "Uncalibrated.",
        "uncertainty": "Unknown.",
        "next_steps": "Review evidence.",
        "citations": ["transaction:1"],
    }
    text, audit = render_interpretation(json.dumps(sections), [{"id": "transaction:1"}])
    assert "[transaction:1]" in text and audit["status"] == "validated_ids"
    sections["citations"] = ["transaction:999"]
    with pytest.raises(HTTPException) as exc:
        render_interpretation(json.dumps(sections), [{"id": "transaction:1"}])
    assert exc.value.status_code == 502


def test_case_and_timeline_timestamps_survive_restart_with_utc_offsets(client, settings):
    from datetime import datetime, timedelta

    case = client.post("/api/v1/cases", json={"title": "UTC timeline"}).json()
    client.post(f"/api/v1/cases/{case['id']}/notes", json={"body": "Timestamped evidence"})
    client.patch(f"/api/v1/cases/{case['id']}", json={"status": "In Review"})
    with TestClient(create_app(settings)) as other:
        stored = other.get(f"/api/v1/cases/{case['id']}").json()
        timestamps = [stored["created_at"], stored["notes"][0]["created_at"]]
        timestamps += [
            event["created_at"]
            for event in other.get(f"/api/v1/cases/{case['id']}/timeline").json()
        ]
        assert all(
            datetime.fromisoformat(value).utcoffset() == timedelta(0) for value in timestamps
        )
        assert datetime.fromisoformat(stored["created_at"]) == datetime.fromisoformat(
            case["created_at"]
        )
