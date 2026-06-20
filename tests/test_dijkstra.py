"""
Тесты алгоритма Дейкстры (dijkstra.py): корректность расстояний,
обработка несвязных вершин, отрицательные веса отклоняются.
См. таблицу 5 отчёта (5 тестов).
"""

import pytest

from src.core.graph import Graph, GraphError
from src.core.algorithms.dijkstra import dijkstra


def sample_graph() -> Graph:
    g = Graph(directed=False)
    g.add_edge("A", "B", 1)
    g.add_edge("B", "C", 2)
    g.add_edge("A", "D", 4)
    g.add_edge("C", "D", 1)
    return g


def test_dijkstra_shortest_distances():
    result = dijkstra(sample_graph(), "A")
    assert result["distances"]["A"] == 0
    assert result["distances"]["B"] == 1
    assert result["distances"]["C"] == 3
    assert result["distances"]["D"] == 4


def test_dijkstra_start_distance_is_zero():
    result = dijkstra(sample_graph(), "B")
    assert result["distances"]["B"] == 0


def test_dijkstra_unreachable_node_is_infinite():
    g = Graph(directed=False)
    g.add_edge("A", "B", 1)
    g.add_node("C")  # изолированная вершина
    result = dijkstra(g, "A")
    assert result["distances"]["C"] == float("inf")


def test_dijkstra_negative_weight_rejected_at_construction():
    g = Graph(directed=False)
    with pytest.raises(GraphError):
        g.add_edge("A", "B", -5)


def test_dijkstra_invalid_start_raises():
    g = sample_graph()
    with pytest.raises(GraphError):
        dijkstra(g, "Z")
