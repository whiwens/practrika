"""
Единый формат шагов выполнения алгоритмов (см. раздел 1.3, 3 отчёта).

Каждый алгоритм возвращает не только конечный результат, но и список
атомарных событий ("шагов"): посещение вершины, рассмотрение ребра,
добавление ребра в результат. Единый формат позволяет использовать
один и тот же механизм воспроизведения в интерфейсе для всех пяти
алгоритмов без дублирования кода визуализации.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


# Типы событий, которые умеет порождать ядро алгоритмов.
VISIT_NODE = "visit_node"
EXAMINE_EDGE = "examine_edge"
ADD_EDGE = "add_edge"
UPDATE_DISTANCE = "update_distance"
DONE = "done"


@dataclass
class Step:
    """Один атомарный шаг выполнения алгоритма."""

    type: str
    node: Optional[str] = None
    edge: Optional[List[str]] = None
    weight: Optional[float] = None
    extra: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        data: Dict[str, Any] = {"type": self.type}
        if self.node is not None:
            data["node"] = self.node
        if self.edge is not None:
            data["edge"] = list(self.edge)
        if self.weight is not None:
            data["weight"] = self.weight
        if self.extra:
            data["extra"] = self.extra
        return data


class StepRecorder:
    """
    Накопитель шагов выполнения алгоритма.

    Алгоритмы не взаимодействуют с пользовательским интерфейсом напрямую,
    а регистрируют свои состояния через объект StepRecorder, который затем
    сериализуется в JSON и передаётся клиенту для пошагового воспроизведения.
    """

    def __init__(self) -> None:
        self._steps: List[Step] = []

    def visit_node(self, node: str, **extra: Any) -> None:
        self._steps.append(Step(type=VISIT_NODE, node=node, extra=extra))

    def examine_edge(self, u: str, v: str, weight: Optional[float] = None, **extra: Any) -> None:
        self._steps.append(Step(type=EXAMINE_EDGE, edge=[u, v], weight=weight, extra=extra))

    def add_edge(self, u: str, v: str, weight: Optional[float] = None, **extra: Any) -> None:
        self._steps.append(Step(type=ADD_EDGE, edge=[u, v], weight=weight, extra=extra))

    def update_distance(self, node: str, distance: float, **extra: Any) -> None:
        self._steps.append(Step(type=UPDATE_DISTANCE, node=node, weight=distance, extra=extra))

    def done(self, **extra: Any) -> None:
        self._steps.append(Step(type=DONE, extra=extra))

    @property
    def steps(self) -> List[Step]:
        return self._steps

    def count_by_type(self, step_type: str) -> int:
        """Используется в тестах для проверки согласованности журнала шагов."""
        return sum(1 for s in self._steps if s.type == step_type)

    def to_list(self) -> List[Dict[str, Any]]:
        return [s.to_dict() for s in self._steps]
