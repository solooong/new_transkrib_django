/* Страница задачи: стриминг журнала, live-статус и прогресс, автообновление по завершении. */

import { apiGet, poll, statusChipHtml } from "./api.js";

const init = JSON.parse(document.getElementById("task-init").textContent);

const terminal = document.getElementById("terminal");
const statusSlot = document.getElementById("status-slot");
const logHint = document.getElementById("log-hint");

let lastLogId = init.last_log_id || 0;
let prevStatus = init.status;
let logCount = terminal ? terminal.querySelectorAll(".log-line").length : 0;
let reloaded = false;

function nearBottom(el) {
  return el.scrollHeight - el.scrollTop - el.clientHeight < 60;
}

function appendLine(line) {
  const stick = nearBottom(terminal);

  const row = document.createElement("div");
  row.className = `log-line lvl-${line.level}`;

  const time = document.createElement("span");
  time.className = "log-t";
  time.textContent = line.t;

  const text = document.createTextNode(line.text);
  row.appendChild(time);
  row.appendChild(text);
  terminal.appendChild(row);

  logCount += 1;
  if (logHint) logHint.textContent = `строк: ${logCount}`;
  if (stick) terminal.scrollTop = terminal.scrollHeight;
}

function updateStatus(data) {
  if (statusSlot) statusSlot.innerHTML = statusChipHtml(data.status, data.progress);

  const wasActive = prevStatus === "pending" || prevStatus === "running";
  const nowTerminal = data.status === "done" || data.status === "error";

  if (wasActive && nowTerminal && !reloaded) {
    reloaded = true;
    // даём пользователю увидеть финальные строки — затем перезагружаем страницу,
    // чтобы отрисовался список результатов
    setTimeout(() => window.location.reload(), 900);
  }
  prevStatus = data.status;
}

const stop = poll(async () => {
  const data = await apiGet(`/api/task/${init.id}/logs/?since=${lastLogId}`);

  (data.logs || []).forEach((line) => {
    appendLine(line);
    lastLogId = Math.max(lastLogId, line.id);
  });

  updateStatus(data);

  if (data.status === "done" || data.status === "error") {
    stop();
  }
}, 1600);

/* курсор в терминале, пока задача активна */
if (prevStatus === "pending" || prevStatus === "running") {
  const cursor = document.createElement("div");
  cursor.className = "log-line lvl-info term-cursor";
  cursor.innerHTML = '<span class="log-t">$</span>';
  terminal.appendChild(cursor);
}
