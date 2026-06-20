"""
Тесты модели графа (graph.py): построение, сериализация/десериализация
JSON, генерация random_graph. См. таблицу 5 отчёта (6 тестов).
"""

import pytest

from src.core.graph import Graph, GraphError


def test_add_node_and_edge_undirected():
    g = Graph(directed=False)
    g.add_edge("A", "B", 2.5)
    assert set(g.nodes) == {"A", "B"}
    assert ("B", 2.5) in g.neighbors("A")
    assert ("A", 2.5) in g.neighbors("B")


def test_directed_edge_is_one_way():
    g = Graph(directed=True)
    g.add_edge("A", "B", 1)
    assert ("B", 1) in g.neighbors("A")
    assert ("A", 1) not in g.neighbors("B")


def test_negative_weight_rejected():
    g = Graph(directed=False)
    with pytest.raises(GraphError):
        g.add_edge("A", "B", -1)


def test_to_dict_and_from_dict_roundtrip():
    g = Graph(directed=False)
    g.add_edge("A", "B", 1.5)
    g.add_node("C", x=10, y=20)
    data = g.to_dict()
    restored = Graph.from_dict(data)
    assert set(restored.nodes) == {"A", "B", "C"}
    assert ("B", 1.5) in restored.neighbors("A")


def test_to_json_and_from_json_roundtrip():
    g = Graph(directed=False)
    g.add_edge("X", "Y", 3)
    text = g.to_json()
    restored = Graph.from_json(text)
    assert restored.edges() == g.edges()


def test_random_graph_is_connected_and_reproducible():
    g1 = Graph.random_graph(10, edge_probability=0.2, seed=7)
    g2 = Graph.random_graph(10, edge_probability=0.2, seed=7)
    assert len(g1) == 10
    assert g1.to_dict() == g2.to_dict()  # воспроизводимость по seed

    # связность: BFS из первой вершины должен достичь всех остальных
    from src.core.algorithms.traversal import bfs
    result = bfs(g1, g1.nodes[0])
    assert set(result["order"]) == set(g1.nodes)
