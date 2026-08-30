import type { Task } from "../types";
import { STATUS_META, fmtNum } from "../data";

/**
 * Версия 2: вместо мониторинга системы — статус Flask-runner'а,
 * который исполняет скрипт транскрибации.
 */
export default function RunnerPanel({ tasks }: { tasks: Task[] }) {
  const running = tasks.filter((t) => t.status === "running").length;
  const pending = tasks.filter((t) => t.status === "pending").length;
  const done = tasks.filter((t) => t.status === "done").length;
  const minutes = Math.round(tasks.filter((t) => t.status === "done").reduce((s, t) => s + t.durationSec, 0) / 60);
  const online = true; // в демо runner всегда доступен

  return (
    <section className="panel panel-hairline p-5" aria-label="Статус runner'а">
      <header className="mb-4 flex items-center gap-2.5">
        <span className="relative flex h-2 w-2">
          <span className={`absolute inline-flex h-full w-full rounded-full opacity-60 ${online ? "animate-ping bg-mint" : ""}`} />
          <span className={`relative inline-flex h-2 w-2 rounded-full ${online ? "bg-mint" : "bg-coral"}`} />
        </span>
        <h2 className="font-display text-[13.5px] font-bold tracking-tight text-snow">Flask-runner</h2>
        <span
          className={`rounded-md border px-2 py-0.5 font-mono text-[10px] font-semibold uppercase tracking-wider ${
            online ? "border-mint/25 bg-mint/10 text-mint" : "border-coral/30 bg-coral/10 text-coral"
          }`}
        >
          {online ? "online" : "offline"}
        </span>
        <span className="ml-auto font-mono text-[10.5px] text-fog-500">:8800 · {running} в работе</span>
      </header>

      <p className="text-[12.5px] leading-relaxed text-fog-400">
        Runner живёт в том же контейнере, запускает <span className="font-mono text-acc">scripts/1.py</span> и шлёт
        журнал, прогресс и текст транскрипта обратно в Django.
      </p>

      <div className="mt-4 grid grid-cols-2 gap-3">
        {[
          { k: "Выполняется", v: running, cls: "text-warm" },
          { k: "В очереди", v: pending, cls: "text-fog-300" },
          { k: "Завершено", v: done, cls: "text-mint" },
          { k: "Минут расшифровано", v: fmtNum.format(minutes), cls: "text-acc" },
        ].map((s) => (
          <div key={s.k} className="rounded-xl border border-ink-700/60 bg-ink-900/50 px-3 py-2.5">
            <p className={`font-display text-[19px] font-bold tabular-nums ${s.cls}`}>{s.v}</p>
            <p className="mt-0.5 font-mono text-[9.5px] uppercase tracking-[0.14em] text-fog-500">{s.k}</p>
          </div>
        ))}
      </div>

      <div className="mt-4 flex flex-wrap gap-x-4 gap-y-1.5">
        {(["running", "pending", "done", "error"] as const).map((s) => {
          const n = tasks.filter((t) => t.status === s).length;
          return (
            <span key={s} className="flex items-center gap-1.5 text-[11px] font-semibold text-fog-400">
              <span className={`h-1.5 w-1.5 rounded-full ${STATUS_META[s].dot}`} />
              {STATUS_META[s].label}
              <span className="font-mono text-fog-500">{n}</span>
            </span>
          );
        })}
      </div>
    </section>
  );
}
