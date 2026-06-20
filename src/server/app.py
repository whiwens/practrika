"""
Серверная часть на Flask (см. раздел 3, 4.2 отчёта).

Сервер предоставляет REST-подобный API, принимающий POST-запросы с
JSON-описанием графа и возвращающий готовый массив шагов алгоритма
для воспроизведения, а также отдаёт статический веб-интерфейс (src/web/).

Маршруты:
    GET  /                  — главная страница интерфейса
    POST /api/run           — запуск алгоритма на переданном графе
    GET  /api/sample/<name> — пример тестового графа из tests/data
"""

from __future__ import annotations

import json
import os

from flask import Flask, jsonify, request, send_from_directory

from src.core.algorithms.dijkstra import dijkstra
from src.core.algorithms.mst import kruskal, prim
from src.core.algorithms.traversal import bfs, dfs
from src.core.graph import Graph, GraphError

WEB_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web")
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "tests", "data")

ALGORITHMS = {
    "bfs": bfs,
    "dfs": dfs,
    "dijkstra": dijkstra,
    "prim": prim,
}

app = Flask(__name__, static_folder=None)


@app.get("/")
def index():
    return send_from_directory(WEB_DIR, "index.html")


@app.get("/static/<path:filename>")
def static_files(filename: str):
    return send_from_directory(os.path.join(WEB_DIR, "static"), filename)


@app.get("/api/sample/<name>")
def sample_graph(name: str):
    path = os.path.join(DATA_DIR, f"{name}.json")
    if not os.path.isfile(path):
        return jsonify({"error": f"Тестовый набор '{name}' не найден"}), 404
    with open(path, "r", encoding="utf-8") as f:
        return jsonify(json.load(f))


@app.post("/api/run")
def run_algorithm():
    """
    Принимает JSON вида:
        {
          "algorithm": "bfs" | "dfs" | "dijkstra" | "prim" | "kruskal",
          "graph": { ... сериализованный граф ... },
          "start": "A"   // не требуется для kruskal
        }
    Возвращает результат алгоритма и журнал шагов StepRecorder.
    """
    payload = request.get_json(silent=True)
    if not payload:
        return jsonify({"error": "Ожидался JSON-объект в теле запроса"}), 400

    algorithm = payload.get("algorithm")
    graph_data = payload.get("graph")
    start = payload.get("start")

    if algorithm not in ALGORITHMS and algorithm != "kruskal":
        return jsonify({"error": f"Неизвестный алгоритм: {algorithm}"}), 400
    if graph_data is None:
        return jsonify({"error": "Отсутствует описание графа ('graph')"}), 400

    try:
        graph = Graph.from_dict(graph_data)
        graph.validate()
    except GraphError as exc:
        return jsonify({"error": str(exc)}), 400
    except (KeyError, TypeError) as exc:
        return jsonify({"error": f"Некорректный формат графа: {exc}"}), 400

    try:
        if algorithm == "kruskal":
            result = kruskal(graph)
        else:
            if not start:
                return jsonify({"error": "Не указана стартовая вершина ('start')"}), 400
            if not graph.has_node(start):
                return jsonify({"error": f"Стартовая вершина '{start}' отсутствует в графе"}), 400
            result = ALGORITHMS[algorithm](graph, start)
    except GraphError as exc:
        return jsonify({"error": str(exc)}), 400

    return jsonify(result)


def create_app() -> Flask:
    return app


if __name__ == "__main__":
    # Хост 0.0.0.0 обязателен для доступа из-за пределов Docker-контейнера.
    app.run(host="0.0.0.0", port=5000, debug=False)
