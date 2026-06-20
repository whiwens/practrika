/*
 * Клиентская логика интерфейса (см. раздел 3, 4.3 отчёта).
 *
 * Состоит из двух независимых частей:
 *   1) Редактор графа на HTML5 Canvas (добавление/удаление вершин и рёбер).
 *   2) Конечный автомат воспроизведения шагов, не связанный напрямую
 *      с логикой построения графа — принимает массив шагов от сервера
 *      и применяет визуальные изменения (подсветку) на каждом такте.
 */

(() => {
  const canvas = document.getElementById("graph-canvas");
  const ctx = canvas.getContext("2d");

  // ---- Состояние графа -------------------------------------------------
  let nodes = [];        // { id, x, y }
  let edges = [];        // { source, target, weight }
  let nextNodeId = 0;
  let currentTool = "node";
  let edgeFirstNode = null;

  // ---- Состояние воспроизведения ---------------------------------------
  let steps = [];
  let stepIndex = 0;
  let playTimer = null;
  let lastResult = null;
  let highlighted = { nodes: new Map(), edges: new Map() }; // id -> color role

  function resizeCanvasToDisplaySize() {
    const rect = canvas.getBoundingClientRect();
    canvas.width = Math.round(rect.width);
    canvas.height = Math.round(rect.height);
  }
  window.addEventListener("resize", () => { resizeCanvasToDisplaySize(); draw(); });

  // ------------------------------------------------------------------ //
  // Редактор графа
  // ------------------------------------------------------------------ //

  function nodeAt(x, y) {
    return nodes.find(n => Math.hypot(n.x - x, n.y - y) < 16);
  }

  function edgeKey(a, b) {
    return [a, b].sort().join("::");
  }

  function addNode(x, y) {
    const id = String.fromCharCode(65 + (nextNodeId % 26)) + (nextNodeId >= 26 ? Math.floor(nextNodeId / 26) : "");
    nextNodeId += 1;
    nodes.push({ id, x, y });
    refreshStartNodeOptions();
    updateStats();
  }

  function addEdgeBetween(a, b) {
    if (a === b) return;
    const key = edgeKey(a, b);
    if (edges.some(e => edgeKey(e.source, e.target) === key)) return;
    const weight = parseFloat(prompt(`Вес ребра ${a}–${b}`, "1.0")) || 1.0;
    if (weight < 0) { alert("Вес ребра не может быть отрицательным."); return; }
    edges.push({ source: a, target: b, weight });
    updateStats();
  }

  function removeNode(id) {
    nodes = nodes.filter(n => n.id !== id);
    edges = edges.filter(e => e.source !== id && e.target !== id);
    refreshStartNodeOptions();
    updateStats();
  }

  function removeEdgeBetween(a, b) {
    const key = edgeKey(a, b);
    edges = edges.filter(e => edgeKey(e.source, e.target) !== key);
    updateStats();
  }

  canvas.addEventListener("click", (e) => {
    const rect = canvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    const hit = nodeAt(x, y);

    if (currentTool === "node") {
      if (!hit) addNode(x, y);
    } else if (currentTool === "edge") {
      if (!hit) return;
      if (!edgeFirstNode) {
        edgeFirstNode = hit.id;
      } else {
        addEdgeBetween(edgeFirstNode, hit.id);
        edgeFirstNode = null;
      }
    }
    draw();
  });

  canvas.addEventListener("contextmenu", (e) => {
    e.preventDefault();
    const rect = canvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    const hit = nodeAt(x, y);
    if (hit) {
      if (confirm(`Удалить вершину ${hit.id}?`)) removeNode(hit.id);
      draw();
      return;
    }
    // проверка клика по ребру (приближённо, по расстоянию до отрезка)
    for (const edge of edges) {
      const a = nodes.find(n => n.id === edge.source);
      const b = nodes.find(n => n.id === edge.target);
      if (!a || !b) continue;
      if (distToSegment(x, y, a.x, a.y, b.x, b.y) < 8) {
        if (confirm(`Удалить ребро ${edge.source}-${edge.target}?`)) {
          removeEdgeBetween(edge.source, edge.target);
        }
        draw();
        return;
      }
    }
  });

  function distToSegment(px, py, x1, y1, x2, y2) {
    const dx = x2 - x1, dy = y2 - y1;
    const lenSq = dx * dx + dy * dy || 1;
    let t = ((px - x1) * dx + (py - y1) * dy) / lenSq;
    t = Math.max(0, Math.min(1, t));
    const projX = x1 + t * dx, projY = y1 + t * dy;
    return Math.hypot(px - projX, py - projY);
  }

  document.querySelectorAll(".tool").forEach(btn => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".tool").forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      currentTool = btn.dataset.tool;
      edgeFirstNode = null;
      document.getElementById("canvas-hint").textContent =
        currentTool === "node"
          ? "Клик по холсту создаёт вершину"
          : "Кликните по двум вершинам, чтобы соединить их ребром";
    });
  });

  document.getElementById("btn-clear").addEventListener("click", () => {
    nodes = []; edges = []; nextNodeId = 0; edgeFirstNode = null;
    clearPlayback();
    refreshStartNodeOptions();
    updateStats();
    draw();
  });

  // ------------------------------------------------------------------ //
  // Отрисовка
  // ------------------------------------------------------------------ //

  const css = getComputedStyle(document.documentElement);
  const COLOR = {
    edge: "#3a4150",
    edgeText: "#8b91a0",
    node: "#262c37",
    nodeBorder: "#454d5e",
    nodeText: "#e8eaed",
    accent: css.getPropertyValue("--accent").trim() || "#5ec8d8",
    result: css.getPropertyValue("--result").trim() || "#d8a657",
  };

  function draw() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // рёбра
    edges.forEach(edge => {
      const a = nodes.find(n => n.id === edge.source);
      const b = nodes.find(n => n.id === edge.target);
      if (!a || !b) return;
      const key = edgeKey(edge.source, edge.target);
      const role = highlighted.edges.get(key);
      ctx.strokeStyle = role === "result" ? COLOR.result : role === "active" ? COLOR.accent : COLOR.edge;
      ctx.lineWidth = role ? 3 : 1.6;
      ctx.beginPath();
      ctx.moveTo(a.x, a.y);
      ctx.lineTo(b.x, b.y);
      ctx.stroke();

      const mx = (a.x + b.x) / 2, my = (a.y + b.y) / 2;
      ctx.fillStyle = COLOR.edgeText;
      ctx.font = "11px monospace";
      ctx.fillText(String(edge.weight), mx + 4, my - 4);
    });

    // вершины
    nodes.forEach(n => {
      const role = highlighted.nodes.get(n.id);
      ctx.beginPath();
      ctx.arc(n.x, n.y, 16, 0, Math.PI * 2);
      ctx.fillStyle = role === "result" ? COLOR.result : role === "active" ? COLOR.accent : COLOR.node;
      ctx.fill();
      ctx.lineWidth = 1.5;
      ctx.strokeStyle = COLOR.nodeBorder;
      ctx.stroke();

      ctx.fillStyle = role ? "#0e1014" : COLOR.nodeText;
      ctx.font = "bold 12px sans-serif";
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      ctx.fillText(n.id, n.x, n.y);
    });
    ctx.textAlign = "start";
    ctx.textBaseline = "alphabetic";
  }

  function updateStats() {
    document.getElementById("graph-stats").textContent = `${nodes.length} вершин · ${edges.length} рёбер`;
  }

  function refreshStartNodeOptions() {
    const sel = document.getElementById("start-node-select");
    sel.innerHTML = "";
    nodes.forEach(n => {
      const opt = document.createElement("option");
      opt.value = n.id; opt.textContent = n.id;
      sel.appendChild(opt);
    });
  }

  document.getElementById("algorithm-select").addEventListener("change", (e) => {
    const needsStart = e.target.value !== "kruskal";
    document.getElementById("start-node-row").style.display = needsStart ? "block" : "none";
  });

  // ------------------------------------------------------------------ //
  // Запуск алгоритма на сервере
  // ------------------------------------------------------------------ //

  function serializeGraph() {
    return {
      directed: false,
      nodes: nodes.map(n => ({ id: n.id, x: n.x, y: n.y })),
      edges: edges.map(e => ({ source: e.source, target: e.target, weight: e.weight })),
    };
  }

  function setStatus(text, isError = false) {
    const el = document.getElementById("run-status");
    el.textContent = text;
    el.classList.toggle("error", isError);
  }

  document.getElementById("btn-run").addEventListener("click", async () => {
    const algorithm = document.getElementById("algorithm-select").value;
    const start = document.getElementById("start-node-select").value;

    if (nodes.length === 0) { setStatus("Граф пуст", true); return; }

    const body = { algorithm, graph: serializeGraph() };
    if (algorithm !== "kruskal") body.start = start;

    setStatus("Выполняется…");
    try {
      const resp = await fetch("/api/run", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      const data = await resp.json();
      if (!resp.ok) {
        setStatus(data.error || "Ошибка выполнения", true);
        return;
      }
      lastResult = data;
      steps = data.steps || [];
      stepIndex = 0;
      setStatus(`Готово: ${steps.length} шагов`);
      renderResult(algorithm, data);
      resetHighlight();
      updateStepCounter();
      draw();
    } catch (err) {
      setStatus("Не удалось связаться с сервером", true);
    }
  });

  function renderResult(algorithm, data) {
    const out = document.getElementById("result-output");
    if (algorithm === "bfs" || algorithm === "dfs") {
      out.innerHTML = `<strong>Порядок обхода:</strong><br>${data.order.join(" → ")}`;
    } else if (algorithm === "dijkstra") {
      const rows = Object.entries(data.distances)
        .map(([k, v]) => `<tr><td>${k}</td><td>${v === Infinity ? "∞" : v}</td></tr>`)
        .join("");
      out.innerHTML = `<strong>Расстояния от старта:</strong><table>${rows}</table>`;
    } else {
      const rows = data.mst_edges.map(([u, v, w]) => `<tr><td>${u}-${v}</td><td>${w}</td></tr>`).join("");
      out.innerHTML = `<strong>Рёбра остова:</strong><table>${rows}</table>
        <p>Суммарный вес: <strong>${data.total_weight}</strong></p>`;
    }
  }

  // ------------------------------------------------------------------ //
  // Конечный автомат воспроизведения шагов (см. раздел 4.3 отчёта)
  // ------------------------------------------------------------------ //

  function resetHighlight() {
    highlighted = { nodes: new Map(), edges: new Map() };
  }

  function clearPlayback() {
    steps = []; stepIndex = 0; lastResult = null;
    resetHighlight();
    stopAutoplay();
    document.getElementById("result-output").innerHTML =
      '<p class="placeholder">Постройте граф и нажмите «Старт», чтобы увидеть результат.</p>';
    updateStepCounter();
  }

  function applyStep(step, direction) {
    // direction: +1 применить шаг вперёд, -1 откатить (упрощённо: активная подсветка временная)
    if (step.type === "visit_node" && direction > 0) {
      highlighted.nodes.set(step.node, "active");
    }
    if (step.type === "examine_edge" && direction > 0) {
      const key = edgeKey(step.edge[0], step.edge[1]);
      if (!highlighted.edges.get(key)) highlighted.edges.set(key, "active");
    }
    if (step.type === "add_edge") {
      const key = edgeKey(step.edge[0], step.edge[1]);
      if (direction > 0) {
        highlighted.edges.set(key, "result");
        highlighted.nodes.set(step.edge[0], "result");
        highlighted.nodes.set(step.edge[1], "result");
      }
    }
  }

  function rebuildHighlightUpTo(index) {
    resetHighlight();
    for (let i = 0; i < index; i++) applyStep(steps[i], +1);
  }

  function updateStepCounter() {
    document.getElementById("step-counter").textContent = `шаг ${stepIndex} / ${steps.length}`;
  }

  function stepForward() {
    if (stepIndex >= steps.length) return;
    applyStep(steps[stepIndex], +1);
    stepIndex += 1;
    updateStepCounter();
    draw();
  }

  function stepBackward() {
    if (stepIndex <= 0) return;
    stepIndex -= 1;
    rebuildHighlightUpTo(stepIndex);
    updateStepCounter();
    draw();
  }

  document.getElementById("btn-step-fwd").addEventListener("click", stepForward);
  document.getElementById("btn-step-back").addEventListener("click", stepBackward);

  function stopAutoplay() {
    if (playTimer) { clearInterval(playTimer); playTimer = null; }
    document.getElementById("btn-play").textContent = "▶ Играть";
  }

  document.getElementById("btn-play").addEventListener("click", () => {
    if (playTimer) { stopAutoplay(); return; }
    if (steps.length === 0) return;
    document.getElementById("btn-play").textContent = "⏸ Пауза";
    const speed = parseInt(document.getElementById("speed-range").value, 10);
    playTimer = setInterval(() => {
      if (stepIndex >= steps.length) { stopAutoplay(); return; }
      stepForward();
    }, speed);
  });

  // ------------------------------------------------------------------ //
  // Импорт / экспорт
  // ------------------------------------------------------------------ //

  document.getElementById("btn-export").addEventListener("click", () => {
    const blob = new Blob([JSON.stringify(serializeGraph(), null, 2)], { type: "application/json" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = "graph.json";
    a.click();
  });

  document.getElementById("import-input").addEventListener("change", async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    try {
      const text = await file.text();
      const data = JSON.parse(text);
      loadGraph(data);
    } catch (err) {
      alert("Не удалось прочитать файл графа: повреждённый или неверный формат JSON.");
    }
    e.target.value = "";
  });

  function loadGraph(data) {
    nodes = (data.nodes || []).map(n => ({ id: n.id, x: n.x ?? Math.random() * 800, y: n.y ?? Math.random() * 500 }));
    edges = (data.edges || []).map(e => ({ source: e.source, target: e.target, weight: e.weight ?? 1.0 }));
    nextNodeId = nodes.length;
    clearPlayback();
    refreshStartNodeOptions();
    updateStats();
    draw();
  }

  document.querySelectorAll("[data-sample]").forEach(btn => {
    btn.addEventListener("click", async () => {
      const resp = await fetch(`/api/sample/${btn.dataset.sample}`);
      if (!resp.ok) { setStatus("Не удалось загрузить пример", true); return; }
      const data = await resp.json();
      loadGraph(data);
      setStatus(`Загружен пример: ${btn.dataset.sample}`);
    });
  });

  // ---- инициализация ----
  resizeCanvasToDisplaySize();
  updateStats();
  updateStepCounter();
  draw();
})();
