"""
Тесты обхода графа (traversal.py): корректность порядка BFS и DFS,
граничные случаи. См. таблицу 5 отчёта (5 тестов).
"""

import pytest

from src.core.graph import Graph, GraphError
from src.core.algorithms.traversal import bfs, dfs


def sample_graph() -> Graph:
    g = Graph(directed=False)
    g.add_edge("A", "B", 1)
    g.add_edge("B", "C", 2)
    g.add_edge("A", "D", 4)
    g.add_edge("C", "D", 1)
    return g


def test_bfs_visits_all_nodes_starting_correctly():
    result = bfs(sample_graph(), "A")
    assert set(result["order"]) == {"A", "B", "C", "D"}
    assert result["order"][0] == "A"


def test_dfs_visits_all_nodes_starting_correctly():
    result = dfs(sample_graph(), "A")
    assert set(result["order"]) == {"A", "B", "C", "D"}
    assert result["order"][0] == "A"


def test_bfs_visits_in_level_order():
    g = Graph(directed=False)
    g.add_edge("A", "B", 1)
    g.add_edge("A", "C", 1)
    g.add_edge("B", "D", 1)
    result = bfs(g, "A")
    # A на уровне 0; B, C на уровне 1; D на уровне 2 -> D не может быть раньше B/C
    assert result["order"].index("D") > result["order"].index("B")


def test_traversal_on_single_node_graph():
    g = Graph(directed=False)
    g.add_node("A")
    assert bfs(g, "A")["order"] == ["A"]
    assert dfs(g, "A")["order"] == ["A"]


def test_traversal_invalid_start_raises():
    g = sample_graph()
    with pytest.raises(GraphError):
        bfs(g, "Z")
    with pytest.raises(GraphError):
        dfs(g, "Z")
