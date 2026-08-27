/* Дашборд: live-метрики системы, график нагрузки, пайплайн и таблица задач. */

import { apiGet, poll, statusChipHtml } from "./api.js";
import { Gauge, LineChart } from "./charts.js";

const esc = (s) =>
  String(s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

/* ---------- инициализация ---------- */

const init = JSON.parse(document.getElementById("metrics-init").textContent);

const gauges = {
  cpu: new Gauge(document.getElementById("g-cpu")),
  ram: new Gauge(document.getElementById("g-ram")),
  gpu: new Gauge(document.getElementById("g-gpu")),
  disk: new Gauge(document.getElementById("g-disk")),
};

const chart = new LineChart(document.getElementById("metrics-chart"), {
  series: ["cpu", "ram", "gpu"],
  colors: { cpu: "#2cd9c8", ram: "#6b93f0", gpu: "#f2a33c" },
});

let history = init.history || [];

function applyCurrent(current) {
  if (!current) return;
  gauges.cpu.set(current.cpu);
  gauges.ram.set(current.ram);
  gauges.gpu.set(current.gpu);
  gauges.disk.set(current.disk);

  const foot = document.getElementById("sys-foot");
  if (foot) foot.textContent = `load ${current.load} · активных задач: ${current.running}`;

  const kpiActive = document.getElementById("kpi-active");
  if (kpiActive && current.running !== undefined) kpiActive.textContent = current.running;
}

applyCurrent(init.current);
chart.draw(history);

/* ---------- поллинг метрик ---------- */

poll(async () => {
  const data = await apiGet("/api/metrics/");
  history = data.history || [];
  applyCurrent(data.current);
  chart.draw(history);
}, 2000);

/* ---------- поллинг задач: таблица + пайплайн ---------- */

const tbody = document.getElementById("tasks-body");

function rowHtml(t) {
  return `
    <tr data-id="${t.id}">
      <td class="mono col-id">${t.id}</td>
      <td>
        <div class="file-cell">
          <span class="file-name">${esc(t.file)}</span>
          <span class="file-meta mono">${esc(t.size)} · ${esc(t.language)}</span>
        </div>
      </td>
      <td class="col-model"><span class="model-chip mono">${esc(t.model)}</span></td>
      <td class="col-status" data-cell="status">${statusChipHtml(t.status, t.progress)}</td>
      <td class="mono col-dur">${esc(t.duration)}</td>
      <td class="mono col-date">${esc(t.created)}</td>
      <td class="col-act"><a class="btn btn-ghost btn-sm" href="${t.url}">Открыть</a></td>
    </tr>`;
}

let lastSnapshot = "";

function renderPipeline(counts, total) {
  const order = ["running", "done", "pending", "error"];
  order.forEach((s) => {
    const seg = document.querySelector(`.seg[data-status="${s}"]`);
    if (seg) seg.style.width = total ? `${((counts[s] || 0) / total) * 100}%` : "0%";
  });

  const legend = document.getElementById("pipeline-legend");
  if (legend) {
    const map = { "dot-running": "running", "dot-done": "done", "dot-pending": "pending", "dot-error": "error" };
    legend.querySelectorAll("span").forEach((span) => {
      const dot = span.querySelector("i");
      const statusClass = dot ? dot.className.split(" ").find((c) => c.startsWith("dot-") && c !== "dot") : null;
      const key = statusClass && map[statusClass];
      if (key) span.querySelector("b").textContent = counts[key] || 0;
    });
  }

  const totalEl = document.getElementById("pipeline-total");
  if (totalEl) totalEl.textContent = `всего ${total}`;
}

poll(async () => {
  const data = await apiGet("/api/tasks/");
  const tasks = data.tasks || [];
  const snapshot = JSON.stringify(tasks);
  if (snapshot === lastSnapshot) return;
  lastSnapshot = snapshot;

  if (tbody) {
    tbody.innerHTML = tasks.length
      ? tasks.map(rowHtml).join("")
      : `<tr><td colspan="7" class="empty-cell">Пока нет ни одной задачи — <a href="/upload/">загрузите первый файл</a>.</td></tr>`;
  }

  const counts = data.counts || {};
  const total = tasks.length;
  renderPipeline(counts, total);

  const kpiTotal = document.getElementById("kpi-total");
  const kpiDone = document.getElementById("kpi-done");
  if (kpiTotal) kpiTotal.textContent = total;
  if (kpiDone) kpiDone.textContent = counts.done || 0;
}, 2500);
