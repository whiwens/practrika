"""
Модель графа (см. раздел 3, 4.1 отчёта).

Класс Graph реализован поверх списка смежности — словаря, сопоставляющего
каждой вершине список пар (сосед, вес). Такое представление выбрано вместо
матрицы смежности, поскольку для разреженных графов учебного размера
список смежности экономичнее по памяти и не требует заранее фиксировать
максимальное число вершин.

Класс поддерживает как ориентированные, так и неориентированные графы
через единый флаг directed.
"""

from __future__ import annotations

import json
import random
from typing import Dict, List, Optional, Tuple


class GraphError(ValueError):
    """Ошибка валидации входных данных графа (см. раздел 4.2 отчёта)."""


class Graph:
    def __init__(self, directed: bool = False) -> None:
        self.directed = directed
        # adjacency: node -> list of (neighbour, weight)
        self._adjacency: Dict[str, List[Tuple[str, float]]] = {}
        # координаты вершин для отрисовки на клиенте (см. раздел 4.3)
        self._positions: Dict[str, Tuple[float, float]] = {}

    # ------------------------------------------------------------------ #
    # Построение графа
    # ------------------------------------------------------------------ #

    def add_node(self, node: str, x: Optional[float] = None, y: Optional[float] = None) -> None:
        if node not in self._adjacency:
            self._adjacency[node] = []
        if x is not None and y is not None:
            self._positions[node] = (x, y)

    def add_edge(self, u: str, v: str, weight: float = 1.0) -> None:
        if weight < 0:
            raise GraphError(f"Вес ребра не может быть отрицательным: {u}-{v} = {weight}")
        self.add_node(u)
        self.add_node(v)
        self._adjacency[u].append((v, weight))
        if not self.directed:
            self._adjacency[v].append((u, weight))

    def remove_node(self, node: str) -> None:
        if node not in self._adjacency:
            return
        del self._adjacency[node]
        self._positions.pop(node, None)
        for n in self._adjacency:
            self._adjacency[n] = [(t, w) for t, w in self._adjacency[n] if t != node]

    def remove_edge(self, u: str, v: str) -> None:
        if u in self._adjacency:
            self._adjacency[u] = [(t, w) for t, w in self._adjacency[u] if t != v]
        if not self.directed and v in self._adjacency:
            self._adjacency[v] = [(t, w) for t, w in self._adjacency[v] if t != u]

    # ------------------------------------------------------------------ #
    # Доступ к структуре
    # ------------------------------------------------------------------ #

    @property
    def nodes(self) -> List[str]:
        return list(self._adjacency.keys())

    def neighbors(self, node: str) -> List[Tuple[str, float]]:
        return list(self._adjacency.get(node, []))

    def edges(self) -> List[Tuple[str, str, float]]:
        """Список рёбер. Для неориентированного графа каждое ребро возвращается один раз."""
        result: List[Tuple[str, str, float]] = []
        seen = set()
        for u, neighbours in self._adjacency.items():
            for v, w in neighbours:
                key = (u, v) if self.directed else tuple(sorted((u, v)))
                if key in seen:
                    continue
                seen.add(key)
                result.append((u, v, w))
        return result

    def has_node(self, node: str) -> bool:
        return node in self._adjacency

    def position(self, node: str) -> Tuple[float, float]:
        return self._positions.get(node, (0.0, 0.0))

    def __len__(self) -> int:
        return len(self._adjacency)

    # ------------------------------------------------------------------ #
    # Валидация (см. раздел 4.2: проверка входных данных на сервере)
    # ------------------------------------------------------------------ #

    def validate(self) -> None:
        """Проверяет, что все рёбра ссылаются на существующие вершины
        и что веса рёбер неотрицательны. Бросает GraphError при нарушении."""
        for u, neighbours in self._adjacency.items():
            if u not in self._adjacency:
                raise GraphError(f"Вершина {u} отсутствует в графе")
            for v, w in neighbours:
                if v not in self._adjacency:
                    raise GraphError(f"Ребро ссылается на несуществующую вершину: {v}")
                if w < 0:
                    raise GraphError(f"Отрицательный вес ребра недопустим: {u}-{v} = {w}")

    # ------------------------------------------------------------------ #
    # Сериализация в JSON (см. раздел 3: Data Layer)
    # ------------------------------------------------------------------ #

    def to_dict(self) -> dict:
        return {
            "directed": self.directed,
            "nodes": [
                {"id": n, "x": self._positions.get(n, (0.0, 0.0))[0],
                 "y": self._positions.get(n, (0.0, 0.0))[1]}
                for n in self._adjacency
            ],
            "edges": [
                {"source": u, "target": v, "weight": w} for u, v, w in self.edges()
            ],
        }

    def to_json(self, **kwargs) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, **kwargs)

    @classmethod
    def from_dict(cls, data: dict) -> "Graph":
        g = cls(directed=bool(data.get("directed", False)))
        for node in data.get("nodes", []):
            g.add_node(node["id"], node.get("x"), node.get("y"))
        for edge in data.get("edges", []):
            weight = float(edge.get("weight", 1.0))
            if weight < 0:
                raise GraphError(
                    f"Отрицательный вес ребра недопустим: "
                    f"{edge['source']}-{edge['target']} = {weight}"
                )
            g.add_node(edge["source"])
            g.add_node(edge["target"])
            g._adjacency[edge["source"]].append((edge["target"], weight))
            if not g.directed:
                g._adjacency[edge["target"]].append((edge["source"], weight))
        return g

    @classmethod
    def from_json(cls, text: str) -> "Graph":
        return cls.from_dict(json.loads(text))

    # ------------------------------------------------------------------ #
    # Генерация тестовых данных (см. раздел 5: random_graph)
    # ------------------------------------------------------------------ #

    @classmethod
    def random_graph(
        cls,
        n_nodes: int,
        edge_probability: float = 0.3,
        directed: bool = False,
        min_weight: float = 1.0,
        max_weight: float = 10.0,
        seed: Optional[int] = None,
    ) -> "Graph":
        """
        Генерирует случайный граф заданного размера.

        Алгоритм сначала строит случайное остовное дерево, гарантируя
        связность тестового набора (важно для тестирования Дейкстры и Прима,
        которые предполагают достижимость всех вершин из стартовой), а затем
        добавляет дополнительные рёбра с вероятностью edge_probability.
        """
        if n_nodes <= 0:
            raise GraphError("Число вершин должно быть положительным")

        rng = random.Random(seed)
        g = cls(directed=directed)
        node_names = [f"N{i}" for i in range(n_nodes)]
        for name in node_names:
            g.add_node(name, x=rng.uniform(0, 800), y=rng.uniform(0, 600))

        if n_nodes == 1:
            return g

        # Случайное остовное дерево для гарантии связности.
        shuffled = node_names[:]
        rng.shuffle(shuffled)
        connected = [shuffled[0]]
        for node in shuffled[1:]:
            other = rng.choice(connected)
            weight = round(rng.uniform(min_weight, max_weight), 2)
            g.add_edge(node, other, weight)
            connected.append(node)

        # Дополнительные рёбра сверх остовного дерева.
        for i, u in enumerate(node_names):
            for v in node_names[i + 1:]:
                if rng.random() < edge_probability:
                    existing = {t for t, _ in g.neighbors(u)}
                    if v not in existing:
                        weight = round(rng.uniform(min_weight, max_weight), 2)
                        g.add_edge(u, v, weight)
        return g
