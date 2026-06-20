"""
Алгоритм Дейкстры для поиска кратчайших путей (см. раздел 4.1 отчёта).

Реализован на основе двоичной кучи (модуль heapq), что даёт асимптотическую
сложность O((V + E) log V). При извлечении вершины с минимальным расстоянием
из кучи проверяется, не была ли она уже посещена ранее с меньшим расстоянием —
приём "ленивого удаления", позволяющий не реализовывать decrease-key вручную
и сохранять корректность результата на графах без рёбер отрицательного веса.
"""

from __future__ import annotations

import heapq
from typing import Any, Dict

from src.core.graph import Graph, GraphError
from src.core.steps import StepRecorder


def dijkstra(graph: Graph, start: str) -> Dict[str, Any]:
    """
    Находит кратчайшие расстояния от start до всех остальных вершин.

    Граф не должен содержать рёбер отрицательного веса — на этапе валидации
    графа (Graph.add_edge / Graph.validate) такие рёбра уже отклоняются.
    """
    if not graph.has_node(start):
        raise GraphError(f"Стартовая вершина {start} отсутствует в графе")

    recorder = StepRecorder()
    distances: Dict[str, float] = {node: float("inf") for node in graph.nodes}
    previous: Dict[str, str] = {}
    distances[start] = 0.0
    recorder.update_distance(start, 0.0)

    visited = set()
    heap = [(0.0, start)]

    while heap:
        dist_u, u = heapq.heappop(heap)
        if u in visited:
            continue  # "ленивое удаление": устаревшая запись в куче
        visited.add(u)
        recorder.visit_node(u)

        for v, weight in graph.neighbors(u):
            recorder.examine_edge(u, v, weight)
            new_dist = dist_u + weight
            if new_dist < distances[v]:
                distances[v] = new_dist
                previous[v] = u
                recorder.update_distance(v, new_dist)
                heapq.heappush(heap, (new_dist, v))

    recorder.done()
    return {
        "distances": distances,
        "previous": previous,
        "steps": recorder.to_list(),
    }
