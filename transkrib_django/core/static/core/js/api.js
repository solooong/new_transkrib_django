/* Общие helpers для live-обновлений интерфейса. */

export function csrfToken() {
  return document.body.dataset.csrf || "";
}

/** fetch с CSRF-заголовком для POST-запросов. */
export function apiPost(url, body = null) {
  return fetch(url, {
    method: "POST",
    headers: {
      "X-CSRFToken": csrfToken(),
      "X-Requested-With": "XMLHttpRequest",
      ...(body ? { "Content-Type": "application/json" } : {}),
    },
    body: body ? JSON.stringify(body) : undefined,
  });
}

export async function apiGet(url) {
  const res = await fetch(url, { headers: { "X-Requested-With": "XMLHttpRequest" } });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

/** Поллинг с автоперезапуском после сбоев; возвращает функцию остановки. */
export function poll(fn, intervalMs) {
  let stopped = false;
  let timer = null;

  async function tick() {
    if (stopped) return;
    try {
      await fn();
    } catch (err) {
      console.warn("[poll] сбой запроса, продолжим через интервал:", err.message);
    }
    if (!stopped) timer = setTimeout(tick, intervalMs);
  }

  tick();
  return () => {
    stopped = true;
    if (timer) clearTimeout(timer);
  };
}

/* ---------- форматирование ---------- */

const p2 = (n) => String(n).padStart(2, "0");

export function fmtClock(ms) {
  const d = new Date(ms);
  return `${p2(d.getHours())}:${p2(d.getMinutes())}:${p2(d.getSeconds())}`;
}

export const STATUS_LABELS = {
  pending: "В очереди",
  running: "Выполняется",
  done: "Завершено",
  error: "Ошибка",
};

/** HTML статус-чипа (+ прогресс-бар для running). Экранирование не нужно: значения серверные. */
export function statusChipHtml(status, progress) {
  if (status === "running") {
    return (
      `<span class="chip chip-running"><i class="chip-dot pulse"></i>Выполняется · ${progress}%</span>` +
      `<span class="progress"><span class="progress-fill stripes" style="width:${progress}%"></span></span>`
    );
  }
  return `<span class="chip chip-${status}"><i class="chip-dot"></i>${STATUS_LABELS[status] || status}</span>`;
}
