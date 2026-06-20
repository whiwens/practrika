"""
Построение минимального остовного дерева: алгоритмы Прима и Краскала
(см. раздел 1.1, 4.1 отчёта).

Алгоритмы Прима и Краскала реализуются оба, хотя индивидуальное задание
требует только один из них: это позволяет в разделе тестирования сравнить
их между собой по числу рассмотренных рёбер и тем самым усилить
аналитическую часть работы.

Алгоритм Прима наращивает дерево от стартовой вершины, на каждом шаге
извлекая из кучи ребро минимального веса, соединяющее текущее дерево
с новой вершиной.

Алгоритм Краскала рассматривает все рёбра графа в порядке возрастания
веса и добавляет очередное ребро в остов, если оно не образует цикл
с уже выбранными рёбрами; проверка цикла выполняется с помощью структуры
данных "система непересекающихся множеств" (Disjoint Set Union, DSU)
с эвристикой сжатия пути.
"""

from __future__ import annotations

import heapq
from typing import Any, Dict, List

from src.core.graph import Graph, GraphError
from src.core.steps import StepRecorder


class DisjointSetUnion:
    """DSU с эвристикой сжатия пути, используется алгоритмом Краскала."""

    def __init__(self, items: List[str]) -> None:
        self._parent = {item: item for item in items}

    def find(self, item: str) -> str:
        root = item
        while self._parent[root] != root:
            root = self._parent[root]
        # сжатие пути
        while self._parent[item] != root:
            self._parent[item], item = root, self._parent[item]
        return root

    def union(self, a: str, b: str) -> bool:
        ra, rb = self.find(a), self.find(b)
        if ra == rb:
            return False
        self._parent[ra] = rb
        return True


def prim(graph: Graph, start: str) -> Dict[str, Any]:
    """Минимальное остовное дерево, алгоритм Прима (наращивание от вершины)."""
    if not graph.has_node(start):
        raise GraphError(f"Стартовая вершина {start} отсутствует в графе")

    recorder = StepRecorder()
    visited = {start}
    recorder.visit_node(start)
    mst_edges: List[List[Any]] = []
    total_weight = 0.0

    heap: List[tuple] = []
    for v, w in graph.neighbors(start):
        heapq.heappush(heap, (w, start, v))

    while heap and len(visited) < len(graph):
        w, u, v = heapq.heappop(heap)
        recorder.examine_edge(u, v, w)
        if v in visited:
            continue
        visited.add(v)
        recorder.visit_node(v)
        recorder.add_edge(u, v, w)
        mst_edges.append([u, v, w])
        total_weight += w
        for nxt, nw in graph.neighbors(v):
            if nxt not in visited:
                heapq.heappush(heap, (nw, v, nxt))

    recorder.done()
    return {
        "mst_edges": mst_edges,
        "total_weight": total_weight,
        "steps": recorder.to_list(),
    }


def kruskal(graph: Graph) -> Dict[str, Any]:
    """Минимальное остовное дерево, алгоритм Краскала (по возрастанию весов рёбер)."""
    recorder = StepRecorder()
    dsu = DisjointSetUnion(graph.nodes)
    mst_edges: List[List[Any]] = []
    total_weight = 0.0

    sorted_edges = sorted(graph.edges(), key=lambda e: e[2])

    for u, v, w in sorted_edges:
        recorder.examine_edge(u, v, w)
        if dsu.union(u, v):
            recorder.add_edge(u, v, w)
            mst_edges.append([u, v, w])
            total_weight += w

    recorder.done()
    return {
        "mst_edges": mst_edges,
        "total_weight": total_weight,
        "steps": recorder.to_list(),
    }
