"""
Обход графа в ширину (BFS) и в глубину (DFS) (см. раздел 4.1 отчёта).

Оба алгоритма реализованы итеративно — через явную очередь (deque) и
явный стек соответственно, без использования рекурсии. Решение принято,
чтобы не упираться в ограничение глубины рекурсии интерпретатора Python
на графах большого размера и чтобы каждый шаг обхода можно было
единообразно регистрировать через StepRecorder в одном и том же цикле.
"""

from __future__ import annotations

from collections import deque
from typing import Any, Dict

from src.core.graph import Graph, GraphError
from src.core.steps import StepRecorder


def bfs(graph: Graph, start: str) -> Dict[str, Any]:
    """Обход графа в ширину. Возвращает порядок посещения и журнал шагов."""
    if not graph.has_node(start):
        raise GraphError(f"Стартовая вершина {start} отсутствует в графе")

    recorder = StepRecorder()
    visited = {start}
    order = [start]
    queue = deque([start])
    recorder.visit_node(start)

    while queue:
        u = queue.popleft()
        for v, w in graph.neighbors(u):
            recorder.examine_edge(u, v, w)
            if v not in visited:
                visited.add(v)
                order.append(v)
                recorder.visit_node(v)
                queue.append(v)

    recorder.done()
    return {"order": order, "steps": recorder.to_list()}


def dfs(graph: Graph, start: str) -> Dict[str, Any]:
    """Обход графа в глубину. Возвращает порядок посещения и журнал шагов."""
    if not graph.has_node(start):
        raise GraphError(f"Стартовая вершина {start} отсутствует в графе")

    recorder = StepRecorder()
    visited = {start}
    order = [start]
    stack = [(start, iter(graph.neighbors(start)))]
    recorder.visit_node(start)

    while stack:
        u, neighbours_iter = stack[-1]
        advanced = False
        for v, w in neighbours_iter:
            recorder.examine_edge(u, v, w)
            if v not in visited:
                visited.add(v)
                order.append(v)
                recorder.visit_node(v)
                stack.append((v, iter(graph.neighbors(v))))
                advanced = True
                break
        if not advanced:
            stack.pop()

    recorder.done()
    return {"order": order, "steps": recorder.to_list()}
