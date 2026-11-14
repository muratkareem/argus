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


def test_search_treats_wildcards_as_literal_text_and_rejects_blank_queries(client):
    client.post("/api/v1/cases", json={"title": "100% evidence_under_review"})
    client.post("/api/v1/cases", json={"title": "100x evidenceXunderXreview"})
    for query in ["%", "_under_"]:
        results = client.get("/api/v1/search", params={"q": query}).json()["results"]
        assert len(results) == 1
        assert results[0]["label"] == "100% evidence_under_review"
    assert client.get("/api/v1/search", params={"q": "   "}).status_code == 422
    assert client.get("/api/v1/search", params={"q": "' OR 1=1 --"}).json()["results"] == []


def test_saved_view_pagination_and_nonfinite_filter_validation(client):
    for name in ["First", "Second"]:
        assert client.post("/api/v1/views", json={"name": name, "filters": {}}).status_code == 201
    assert [view["name"] for view in client.get("/api/v1/views?limit=1&offset=1").json()] == [
        "First"
    ]
    assert client.get("/api/v1/views?limit=501").status_code == 422
    assert client.post("/api/v1/views", json={"name": "   ", "filters": {}}).status_code == 422
    for key in ["min_amount", "max_amount", "min_time", "max_time"]:
        assert client.get("/api/v1/transactions", params={key: "inf"}).status_code == 422


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


def test_graph_limits_are_explicit_and_keep_edges_inside_returned_nodes(client):
    with client.app.state.session_factory() as session:
        seed_graph(session)
    graph = client.get("/api/v1/intelligence/graph?node_limit=2").json()
    assert graph["truncated"] is True
    assert len(graph["nodes"]) == 2
    assert graph["total_entities"] > 2
    ids = {node["data"]["id"] for node in graph["nodes"]}
    assert all(
        edge["data"]["source"] in ids and edge["data"]["target"] in ids for edge in graph["edges"]
    )
    neighborhood = client.get(
        "/api/v1/intelligence/graph?root=device-1&depth=3&node_limit=2"
    ).json()
    assert neighborhood["truncated"] is True
    assert len(neighborhood["nodes"]) == 2
    assert "device-1" in {node["data"]["id"] for node in neighborhood["nodes"]}
    assert client.get("/api/v1/intelligence/graph?node_limit=2001").status_code == 422


def test_shared_device_counts_distinct_accounts_and_filters_relations(client):
    from app.db import Relationship

    with client.app.state.session_factory() as session:
        seed_graph(session)
        session.add(Relationship(source="account-1", target="device-1", kind="uses"))
        session.commit()
    graph = client.get("/api/v1/intelligence/graph?root=device-1&depth=1&relation=uses").json()
    device = next(node for node in graph["nodes"] if node["data"]["id"] == "device-1")
    assert device["data"]["shared_accounts"] == 3
    assert len(graph["nodes"]) == 4
    assert all(edge["data"]["label"] == "uses" for edge in graph["edges"])
    devices = client.get("/api/v1/intelligence/graph?shared_only=true&kind=Device").json()
    assert [node["data"]["id"] for node in devices["nodes"]] == ["device-1"]


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


def test_language_model_routes_are_removed(client):
    assert client.get("/api/v1/copilot/context?case_id=1").status_code == 404
    assert client.post("/api/v1/copilot", json={"question": "test"}).status_code == 404


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
