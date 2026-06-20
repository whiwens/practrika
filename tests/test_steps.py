"""
Тесты согласованности журнала шагов (steps.py): соответствие числа
событий visit_node числу достижимых вершин, соответствие событий
add_edge итоговому списку mst_edges. См. таблицу 5 отчёта (4 теста).
"""

from src.core.graph import Graph
from src.core.steps import StepRecorder, VISIT_NODE, ADD_EDGE
from src.core.algorithms.traversal import bfs
from src.core.algorithms.mst import prim, kruskal


def sample_graph() -> Graph:
    g = Graph(directed=False)
    g.add_edge("A", "B", 1)
    g.add_edge("B", "C", 2)
    g.add_edge("A", "D", 4)
    g.add_edge("C", "D", 1)
    return g


def test_step_recorder_basic_serialization():
    rec = StepRecorder()
    rec.visit_node("A")
    rec.examine_edge("A", "B", 1.5)
    rec.add_edge("A", "B", 1.5)
    data = rec.to_list()
    assert data[0] == {"type": VISIT_NODE, "node": "A"}
    assert data[2]["type"] == ADD_EDGE
    assert data[2]["edge"] == ["A", "B"]


def test_visit_node_count_matches_reachable_nodes():
    g = sample_graph()
    result = bfs(g, "A")
    visit_events = [s for s in result["steps"] if s["type"] == "visit_node"]
    assert len(visit_events) == len(set(result["order"]))


def test_add_edge_events_match_mst_edges_prim():
    g = sample_graph()
    result = prim(g, "A")
    add_edge_events = [tuple(sorted(s["edge"])) for s in result["steps"] if s["type"] == "add_edge"]
    mst_pairs = [tuple(sorted((u, v))) for u, v, w in result["mst_edges"]]
    assert sorted(add_edge_events) == sorted(mst_pairs)


def test_add_edge_events_match_mst_edges_kruskal():
    g = sample_graph()
    result = kruskal(g)
    add_edge_events = [tuple(sorted(s["edge"])) for s in result["steps"] if s["type"] == "add_edge"]
    mst_pairs = [tuple(sorted((u, v))) for u, v, w in result["mst_edges"]]
    assert sorted(add_edge_events) == sorted(mst_pairs)
