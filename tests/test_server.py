"""
Тесты серверной части на Flask (см. раздел 4.2 отчёта): маршрут
/api/run и валидация входных данных.
"""

import pytest

from src.server.app import app


@pytest.fixture()
def client():
    app.config.update(TESTING=True)
    with app.test_client() as c:
        yield c


def small_graph_payload():
    return {
        "directed": False,
        "nodes": [{"id": "A", "x": 0, "y": 0}, {"id": "B", "x": 1, "y": 1}, {"id": "C", "x": 2, "y": 2}],
        "edges": [{"source": "A", "target": "B", "weight": 1}, {"source": "B", "target": "C", "weight": 1}],
    }


def test_index_page_served(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert "Визуализатор".encode("utf-8") in resp.data


def test_run_bfs_returns_steps(client):
    resp = client.post("/api/run", json={
        "algorithm": "bfs", "start": "A", "graph": small_graph_payload(),
    })
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["order"][0] == "A"
    assert len(data["steps"]) > 0


def test_run_kruskal_does_not_require_start(client):
    resp = client.post("/api/run", json={
        "algorithm": "kruskal", "graph": small_graph_payload(),
    })
    assert resp.status_code == 200
    assert resp.get_json()["total_weight"] == 2.0


def test_run_rejects_negative_weight(client):
    payload = small_graph_payload()
    payload["edges"] = [{"source": "A", "target": "B", "weight": -3}]
    resp = client.post("/api/run", json={
        "algorithm": "dijkstra", "start": "A", "graph": payload,
    })
    assert resp.status_code == 400
    assert "error" in resp.get_json()


def test_run_rejects_missing_start_for_bfs(client):
    resp = client.post("/api/run", json={
        "algorithm": "bfs", "graph": small_graph_payload(),
    })
    assert resp.status_code == 400


def test_run_rejects_unknown_algorithm(client):
    resp = client.post("/api/run", json={
        "algorithm": "astar", "start": "A", "graph": small_graph_payload(),
    })
    assert resp.status_code == 400


def test_sample_endpoint_returns_known_sample(client):
    resp = client.get("/api/sample/small_undirected")
    assert resp.status_code == 200
    data = resp.get_json()
    assert "nodes" in data and "edges" in data


def test_sample_endpoint_404_for_unknown_sample(client):
    resp = client.get("/api/sample/does_not_exist")
    assert resp.status_code == 404
