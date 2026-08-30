/* Общий модуль: живой индикатор доступности Flask-runner'а в шапке. */

import { poll, apiGet } from "./api.js";

const pill = document.getElementById("runner-pill");
const text = document.getElementById("runner-pill-text");

function setState(online) {
  if (!pill || !text) return;
  pill.dataset.state = online ? "online" : "offline";
  text.textContent = online ? "runner онлайн" : "runner офлайн";
  pill.title = online
    ? "Flask-runner работает и принимает задачи"
    : "Flask-runner недоступен — задачи не будут обрабатываться";
}

if (pill) {
  poll(async () => {
    const data = await apiGet("/api/runner-status/");
    setState(Boolean(data.online));
  }, 5000);
}
