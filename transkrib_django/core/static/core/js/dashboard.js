/* Дашборд: live-обновление таблицы транскрибаций и KPI (polling /api/tasks/). */

import { apiGet, poll, statusChipHtml } from "./api.js";

const body = document.getElementById("tasks-body");

function setKpi(id, value) {
  const el = document.getElementById(id);
  if (el) el.textContent = value;
}

function renderRow(t) {
  const tr = document.createElement("tr");
  tr.dataset.id = t.id;
  tr.innerHTML =
    `<td class="mono col-id">${t.id}</td>` +
    `<td><div class="file-cell">` +
    `<span class="file-name">${t.file}</span>` +
    `<span class="file-meta mono">${t.size} · ${t.language}</span></div></td>` +
    `<td class="col-model"><span class="model-chip mono">${t.model}</span></td>` +
    `<td class="col-status" data-cell="status">${statusChipHtml(t.status, t.progress)}</td>` +
    `<td class="mono col-dur">${t.duration}</td>` +
    `<td class="mono col-date">${t.created}</td>` +
    `<td class="col-act"><a class="btn btn-ghost btn-sm" href="${t.url}">Открыть</a></td>`;
  return tr;
}

function render(tasks, counts, minutes) {
  // убираем строку «пусто», если она есть
  const empty = document.getElementById("tasks-empty");

  if (!tasks.length) {
    body.innerHTML =
      '<tr id="tasks-empty"><td colspan="7" class="empty-cell">' +
      'Пока нет ни одной транскрибации — <a href="/upload/">загрузите первый файл</a>.</td></tr>';
  } else {
    if (empty) empty.remove();
    body.innerHTML = "";
    tasks.forEach((t) => body.appendChild(renderRow(t)));
  }

  setKpi("kpi-total", counts.pending + counts.running + counts.done + counts.error);
  setKpi("kpi-done", counts.done);
  setKpi("kpi-active", counts.pending + counts.running);
  setKpi("kpi-minutes", minutes);
}

poll(async () => {
  const data = await apiGet("/api/tasks/");
  render(data.tasks, data.counts, data.minutes ?? 0);
}, 2500);
