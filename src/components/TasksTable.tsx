import type { Task } from "../types";
import { STATUS_META, fmtDay, fmtDurLong, fmtSize } from "../data";
import { IcAudioFile, IcChevronR } from "../icons";

export function StatusChip({ status, progress }: { status: Task["status"]; progress?: number }) {
  const m = STATUS_META[status];
  return (
    <span className={`inline-flex items-center gap-1.5 rounded-md border px-2 py-1 text-[11px] font-bold leading-none ${m.chip}`}>
      <span className={`h-1.5 w-1.5 rounded-full ${m.dot}`} />
      {m.label}
      {status === "running" && progress !== undefined && (
        <span className="ml-0.5 font-mono font-semibold">{Math.floor(progress)}%</span>
      )}
    </span>
  );
}

function ext(name: string) {
  const i = name.lastIndexOf(".");
  return i >= 0 ? name.slice(i + 1).toUpperCase() : "FILE";
}

export default function TasksTable({
  tasks,
  onOpen,
  compact = false,
}: {
  tasks: Task[];
  onOpen: (t: Task) => void;
  compact?: boolean;
}) {
  return (
    <div className="overflow-x-auto">
      {/* шапка */}
      <div className="grid min-w-[640px] grid-cols-[minmax(0,2.5fr)_minmax(0,1.1fr)_minmax(0,0.8fr)_minmax(0,1.25fr)_minmax(0,1fr)_36px] items-center gap-3 border-b border-ink-700/60 px-4 pb-2.5 pt-1">
        {["Файл", "Модель", "Длина", "Статус", "Создано", ""].map((h, i) => (
          <p key={i} className="font-mono text-[10px] uppercase tracking-[0.18em] text-fog-500">
            {h}
          </p>
        ))}
      </div>

      {tasks.map((t, idx) => (
        <button
          key={t.id}
          onClick={() => onOpen(t)}
          className={`group anim-fade-up grid w-full min-w-[640px] grid-cols-[minmax(0,2.5fr)_minmax(0,1.1fr)_minmax(0,0.8fr)_minmax(0,1.25fr)_minmax(0,1fr)_36px] items-center gap-3 border-b border-ink-700/40 px-4 py-3 text-left transition-all duration-200 hover:bg-ink-800/60 ${
            t.status === "running" ? "shadow-[inset_3px_0_0_rgba(242,163,60,0.65)]" : ""
          } ${t.status === "error" ? "shadow-[inset_3px_0_0_rgba(242,109,100,0.5)]" : ""}`}
          style={{ animationDelay: `${Math.min(idx, 12) * 40}ms` }}
        >
          {/* файл */}
          <div className="flex min-w-0 items-center gap-3">
            <span className="grid h-9 w-9 shrink-0 place-items-center rounded-lg border border-ink-600/60 bg-ink-800/80 text-acc transition-all duration-300 group-hover:border-acc/40 group-hover:text-snow">
              <IcAudioFile className="h-[18px] w-[18px]" />
            </span>
            <div className="min-w-0">
              <p className="truncate text-[13.5px] font-bold text-snow transition-colors group-hover:text-acc">
                {t.fileName}
              </p>
              <p className="mt-0.5 flex items-center gap-2 font-mono text-[10.5px] text-fog-500">
                <span className="rounded bg-ink-700/80 px-1 py-px text-[9.5px] font-bold tracking-wider text-fog-300">
                  {ext(t.fileName)}
                </span>
                {fmtSize(t.sizeMb)}
                <span className="text-ink-600">·</span>
                <span className="hidden sm:inline">{t.id}</span>
              </p>
            </div>
          </div>

          {/* модель */}
          <p className="truncate font-mono text-[11.5px] text-fog-400">{t.model}</p>

          {/* длительность */}
          <p className="font-mono text-[11.5px] tabular-nums text-fog-300">{fmtDurLong(t.durationSec)}</p>

          {/* статус */}
          <div className="min-w-0">
            <StatusChip status={t.status} progress={t.progress} />
            {t.status === "running" && (
              <div className="mt-1.5 h-1 overflow-hidden rounded-full bg-ink-600/60">
                <div
                  className="stripes-anim h-full rounded-full bg-warm transition-all duration-700"
                  style={{ width: `${t.progress}%` }}
                />
              </div>
            )}
          </div>

          {/* создано */}
          <p className="truncate text-[12px] text-fog-400">{fmtDay(t.createdAt)}</p>

          <IcChevronR className="h-4 w-4 justify-self-end text-fog-500 transition-all duration-200 group-hover:translate-x-0.5 group-hover:text-acc" />
        </button>
      ))}

      {!compact && tasks.length === 0 && null}
    </div>
  );
}
