"""
Тесты построения минимального остовного дерева (mst.py):
корректность Прима и Краскала, совпадение суммарного веса,
цикл не образуется. См. таблицу 5 отчёта (7 тестов).
"""

import pytest

from src.core.graph import Graph, GraphError
from src.core.algorithms.mst import prim, kruskal


def sample_graph() -> Graph:
    g = Graph(directed=False)
    g.add_edge("A", "B", 1)
    g.add_edge("B", "C", 2)
    g.add_edge("A", "D", 4)
    g.add_edge("C", "D", 1)
    return g


def test_prim_total_weight():
    result = prim(sample_graph(), "A")
    assert result["total_weight"] == 4
    assert len(result["mst_edges"]) == 3


def test_kruskal_total_weight():
    result = kruskal(sample_graph())
    assert result["total_weight"] == 4
    assert len(result["mst_edges"]) == 3


def test_prim_and_kruskal_weights_match():
    prim_result = prim(sample_graph(), "A")
    kruskal_result = kruskal(sample_graph())
    assert prim_result["total_weight"] == kruskal_result["total_weight"]


def test_mst_edge_count_is_n_minus_1():
    g = sample_graph()
    result = prim(g, "A")
    assert len(result["mst_edges"]) == len(g) - 1


def test_kruskal_does_not_form_cycle():
    # Треугольник: ребро C-A с большим весом не должно войти в остов,
    # иначе образовался бы цикл.
    g = sample_graph()
    g.add_edge("C", "A", 100)
    result = kruskal(g)
    chosen = {tuple(sorted((u, v))) for u, v, w in result["mst_edges"]}
    assert ("A", "C") not in chosen


def test_prim_on_random_graph_matches_kruskal():
    g = Graph.random_graph(15, edge_probability=0.25, seed=3)
    prim_result = prim(g, g.nodes[0])
    kruskal_result = kruskal(g)
    assert prim_result["total_weight"] == pytest.approx(kruskal_result["total_weight"])


def test_prim_invalid_start_raises():
    g = sample_graph()
    with pytest.raises(GraphError):
        prim(g, "Z")
