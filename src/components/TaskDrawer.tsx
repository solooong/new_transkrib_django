import { useEffect, useMemo, useRef, useState } from "react";
import type { Task } from "../types";
import {
  fmtClock,
  fmtDay,
  fmtDur,
  fmtDurLong,
  fmtNum,
  fmtSize,
  mulberry32,
  resultFiles,
  seedFromId,
} from "../data";
import { StatusChip } from "./TasksTable";
import {
  IcAlert,
  IcClose,
  IcDoc,
  IcDownload,
  IcGlobe,
  IcLayers,
  IcPause,
  IcPlay,
  IcRetry,
  IcTerminal,
  IcTrash,
  IcWave,
} from "../icons";

type Tab = "transcript" | "log" | "files";

/* ---------------- мини-плеер с волной ---------------- */

function WavePlayer({ task }: { task: Task }) {
  const dur = task.durationSec;
  const [playing, setPlaying] = useState(false);
  const [pos, setPos] = useState(0);
  const barRef = useRef<HTMLDivElement>(null);

  const bars = useMemo(() => {
    const rnd = mulberry32(seedFromId(task.id));
    return Array.from({ length: 64 }, () => 0.18 + rnd() * 0.82);
  }, [task.id]);

  useEffect(() => {
    if (!playing) return;
    const id = setInterval(() => {
      setPos((p) => {
        if (p + 0.25 >= dur) {
          setPlaying(false);
          return dur;
        }
        return p + 0.25;
      });
    }, 250);
    return () => clearInterval(id);
  }, [playing, dur]);

  const seek = (e: React.MouseEvent) => {
    const el = barRef.current;
    if (!el) return;
    const r = el.getBoundingClientRect();
    const f = Math.max(0, Math.min(1, (e.clientX - r.left) / r.width));
    setPos(f * dur);
  };

  const played = pos / dur;

  return (
    <div className="rounded-xl border border-ink-700/70 bg-ink-900/70 p-3.5">
      <div className="flex items-center gap-3.5">
        <button
          onClick={() => setPlaying((p) => (pos >= dur ? (setPos(0), true) : !p))}
          className="grid h-11 w-11 shrink-0 place-items-center rounded-full border border-acc/45 bg-acc/15 text-acc transition-all duration-200 hover:scale-105 hover:bg-acc/25 hover:shadow-[0_0_24px_-4px_rgba(44,217,200,0.5)] active:scale-95"
          aria-label={playing ? "Пауза" : "Воспроизвести"}
        >
          {playing ? <IcPause className="h-5 w-5" /> : <IcPlay className="ml-0.5 h-5 w-5" />}
        </button>
        <div className="min-w-0 flex-1">
          <div
            ref={barRef}
            onClick={seek}
            className="flex h-12 cursor-pointer items-end gap-[2.5px] px-1"
            role="slider"
            aria-label="Перемотка"
            aria-valuenow={Math.round(pos)}
            aria-valuemin={0}
            aria-valuemax={dur}
          >
            {bars.map((b, i) => {
              const on = i / bars.length <= played;
              return (
                <span
                  key={i}
                  className={`min-w-0 flex-1 rounded-full transition-colors duration-150 ${
                    on ? "bg-acc" : "bg-ink-600/80"
                  } ${playing && on ? "opacity-100" : "opacity-90"}`}
                  style={{ height: `${b * 100}%`, boxShadow: on ? "0 0 8px rgba(44,217,200,0.35)" : undefined }}
                />
              );
            })}
          </div>
          <div className="mt-1.5 flex items-center justify-between font-mono text-[10.5px] tabular-nums text-fog-500">
            <span className="text-acc">{fmtDur(pos)}</span>
            <span>{fmtDur(dur)}</span>
          </div>
        </div>
      </div>
      <p className="mt-2 border-t border-ink-700/50 pt-2 text-[10.5px] text-fog-500">
        Предпрослушивание синтезировано для демо · клик по волне или реплике — перемотка
      </p>
    </div>
  );
}

/* ---------------- вкладки ---------------- */

function TranscriptTab({ task }: { task: Task }) {
  const segs = task.transcript ?? [];
  return (
    <div className="space-y-3">
      <WavePlayer task={task} />
      <div className="max-h-[340px] space-y-1 overflow-y-auto pr-1.5">
        {segs.map((s, i) => (
          <div
            key={i}
            className="group flex gap-3 rounded-lg border border-transparent px-3 py-2.5 transition-all duration-200 hover:border-ink-600/70 hover:bg-ink-800/60"
          >
            <span className="mt-0.5 shrink-0 font-mono text-[11px] font-semibold tabular-nums text-acc/80 transition group-hover:text-acc">
              {fmtDur(s.start)}
            </span>
            <div className="min-w-0">
              {task.diarization && (
                <span
                  className={`mb-0.5 inline-block rounded px-1.5 py-px font-mono text-[9.5px] font-bold uppercase tracking-wider ${
                    s.speaker === "Спикер 1" ? "bg-skyx/15 text-skyx" : "bg-warm/15 text-warm"
                  }`}
                >
                  {s.speaker}
                </span>
              )}
              <p className="text-[13px] leading-relaxed text-fog-300 transition group-hover:text-snow">{s.text}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function LogTab({ task }: { task: Task }) {
  const ref = useRef<HTMLDivElement>(null);
  useEffect(() => {
    const el = ref.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [task.log.length, task.status]);

  const colors: Record<string, string> = {
    info: "text-fog-300",
    ok: "text-mint",
    warn: "text-warm",
    err: "text-coral",
  };

  return (
    <div
      ref={ref}
      className="max-h-[430px] overflow-y-auto rounded-xl border border-ink-700/70 bg-[#080d18] p-3.5 font-mono text-[11.5px] leading-[1.75]"
    >
      {task.log.map((l, i) => (
        <p key={i} className="log-line flex gap-2.5">
          <span className="shrink-0 select-none text-fog-500/70">{fmtClock(l.t)}</span>
          <span className={colors[l.level]}>{l.text}</span>
        </p>
      ))}
      {(task.status === "running" || task.status === "pending") && (
        <p className="term-cursor text-acc">
          <span className="text-fog-500">$</span>
        </p>
      )}
    </div>
  );
}

function FilesTab({
  task,
  onDownload,
  onRetry,
}: {
  task: Task;
  onDownload: (t: Task, name: string) => void;
  onRetry: (id: string) => void;
}) {
  if (task.status === "error") {
    return (
      <div className="rounded-xl border border-coral/30 bg-coral/8 p-5">
        <div className="flex items-start gap-3">
          <span className="grid h-9 w-9 shrink-0 place-items-center rounded-lg border border-coral/40 bg-coral/15 text-coral">
            <IcAlert className="h-[18px] w-[18px]" />
          </span>
          <div>
            <p className="text-[13.5px] font-bold text-coral">Процесс упал с кодом 1</p>
            <p className="mt-1.5 font-mono text-[11.5px] leading-relaxed text-fog-300">{task.error}</p>
            <button
              onClick={() => onRetry(task.id)}
              className="mt-4 inline-flex items-center gap-2 rounded-lg border border-warm/40 bg-warm/12 px-3.5 py-2 text-[12.5px] font-bold text-warm transition-all hover:-translate-y-px hover:bg-warm/20"
            >
              <IcRetry className="h-4 w-4" /> Повторить попытку
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (task.status !== "done") {
    return (
      <div className="rounded-xl border border-ink-700/70 bg-ink-900/60 p-6 text-center">
        <p className="font-display text-[34px] font-bold tabular-nums text-warm">
          {Math.floor(task.progress)}
          <span className="text-lg">%</span>
        </p>
        <div className="mx-auto mt-3 h-1.5 max-w-[240px] overflow-hidden rounded-full bg-ink-600/60">
          <div className="stripes-anim h-full rounded-full bg-warm transition-all duration-700" style={{ width: `${task.progress}%` }} />
        </div>
        <p className="mt-3 text-[12.5px] text-fog-400">
          {task.status === "pending" ? "Задача ждёт освобождения GPU…" : "Идёт распознавание — результаты появятся здесь"}
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-2">
      {resultFiles(task).map((f) => (
        <div
          key={f.name}
          className="group flex items-center gap-3 rounded-xl border border-ink-700/70 bg-ink-900/60 px-3.5 py-3 transition-all duration-200 hover:border-acc/35 hover:bg-ink-800/70"
        >
          <span className="grid h-9 w-9 shrink-0 place-items-center rounded-lg bg-ink-700/70 text-fog-300 transition group-hover:text-acc">
            <IcDoc className="h-[18px] w-[18px]" />
          </span>
          <div className="min-w-0 flex-1">
            <p className="truncate font-mono text-[12.5px] font-semibold text-snow">{f.name}</p>
            <p className="font-mono text-[10.5px] text-fog-500">{f.size} · media/results/{task.id}/</p>
          </div>
          <button
            onClick={() => onDownload(task, f.name)}
            className="flex items-center gap-1.5 rounded-lg border border-acc/35 bg-acc/10 px-3 py-1.5 text-[11.5px] font-bold text-acc opacity-80 transition-all duration-200 hover:opacity-100 hover:shadow-[0_4px_16px_-4px_rgba(44,217,200,0.5)]"
          >
            <IcDownload className="h-3.5 w-3.5" /> Скачать
          </button>
        </div>
      ))}
    </div>
  );
}

/* ---------------- сама панель ---------------- */

export default function TaskDrawer({
  task,
  onClose,
  onRetry,
  onDelete,
  onDownload,
}: {
  task: Task;
  onClose: () => void;
  onRetry: (id: string) => void;
  onDelete: (id: string) => void;
  onDownload: (t: Task, name: string) => void;
}) {
  const [tab, setTab] = useState<Tab>(() =>
    task.status === "done" ? "transcript" : task.status === "error" ? "log" : "log",
  );

  useEffect(() => {
    const h = (e: KeyboardEvent) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", h);
    return () => window.removeEventListener("keydown", h);
  }, [onClose]);

  const tabs: { id: Tab; label: string; icon: typeof IcWave; show: boolean }[] = [
    { id: "transcript", label: "Транскрипт", icon: IcWave, show: task.status === "done" },
    { id: "log", label: "Журнал", icon: IcTerminal, show: true },
    { id: "files", label: "Результаты", icon: IcDoc, show: true },
  ];

  return (
    <div className="fixed inset-0 z-50">
      <div className="anim-fade absolute inset-0 bg-ink-950/72 backdrop-blur-[3px]" onClick={onClose} />
      <aside className="anim-drawer absolute inset-y-0 right-0 flex w-full max-w-[540px] flex-col border-l border-ink-700/70 bg-ink-900 shadow-[-40px_0_80px_-30px_rgba(2,6,16,0.9)]">
        {/* шапка */}
        <header className="border-b border-ink-700/60 px-5 pb-4 pt-5">
          <div className="flex items-start gap-3">
            <div className="min-w-0 flex-1">
              <div className="flex items-center gap-2">
                <p className="truncate font-display text-[15px] font-bold tracking-tight text-snow">{task.fileName}</p>
              </div>
              <p className="mt-1 font-mono text-[10.5px] uppercase tracking-wider text-fog-500">
                {task.id} · создан {fmtDay(task.createdAt)}
              </p>
            </div>
            <StatusChip status={task.status} progress={task.progress} />
            <button
              onClick={onClose}
              className="rounded-lg p-1.5 text-fog-400 transition hover:bg-ink-700 hover:text-snow"
              aria-label="Закрыть панель"
            >
              <IcClose className="h-[18px] w-[18px]" />
            </button>
          </div>

          {/* мета */}
          <div className="mt-4 grid grid-cols-2 gap-2 sm:grid-cols-4">
            {[
              { k: "Размер", v: fmtSize(task.sizeMb) },
              { k: "Длительность", v: fmtDurLong(task.durationSec) },
              { k: "Язык", v: task.language, icon: IcGlobe },
              { k: "Модель", v: task.model, icon: IcLayers },
            ].map((m) => (
              <div key={m.k} className="rounded-lg border border-ink-700/60 bg-ink-850/70 px-2.5 py-2">
                <p className="font-mono text-[9.5px] uppercase tracking-[0.14em] text-fog-500">{m.k}</p>
                <p className="mt-0.5 flex items-center gap-1 truncate font-mono text-[11px] font-semibold text-fog-300">
                  {m.icon && <m.icon className="h-3 w-3 shrink-0 text-fog-500" />}
                  <span className="truncate">{m.v}</span>
                </p>
              </div>
            ))}
          </div>

          {task.status === "done" && (
            <div className="mt-3 flex flex-wrap items-center gap-x-4 gap-y-1 rounded-lg border border-mint/20 bg-mint/6 px-3 py-2 font-mono text-[11px] text-fog-300">
              <span>
                слов: <b className="text-snow">{fmtNum.format(task.words ?? 0)}</b>
              </span>
              <span>
                точность: <b className="text-mint">{task.confidence?.toFixed(1)}%</b>
              </span>
              <span>
                спикеров: <b className="text-snow">{task.speakers}</b>
              </span>
              <span className="ml-auto text-fog-500">готово {task.finishedAt ? fmtClock(task.finishedAt) : "—"}</span>
            </div>
          )}
        </header>

        {/* вкладки */}
        <div className="flex gap-1 border-b border-ink-700/60 px-5 pt-3">
          {tabs
            .filter((t) => t.show)
            .map((t) => {
              const Icon = t.icon;
              const active = tab === t.id;
              return (
                <button
                  key={t.id}
                  onClick={() => setTab(t.id)}
                  className={`relative flex items-center gap-2 rounded-t-lg px-3.5 py-2.5 text-[12.5px] font-bold transition-colors duration-200 ${
                    active ? "text-acc" : "text-fog-400 hover:text-snow"
                  }`}
                >
                  <Icon className="h-4 w-4" />
                  {t.label}
                  <span
                    className={`absolute inset-x-2 -bottom-px h-[2px] rounded-full bg-acc transition-all duration-300 ${
                      active ? "opacity-100" : "opacity-0"
                    }`}
                  />
                </button>
              );
            })}
        </div>

        {/* содержимое */}
        <div className="min-h-0 flex-1 overflow-y-auto px-5 py-4">
          {tab === "transcript" && <TranscriptTab task={task} />}
          {tab === "log" && <LogTab task={task} />}
          {tab === "files" && <FilesTab task={task} onDownload={onDownload} onRetry={onRetry} />}
        </div>

        {/* действия */}
        <footer className="flex items-center gap-2 border-t border-ink-700/60 px-5 py-3.5">
          {task.status === "error" && (
            <button
              onClick={() => onRetry(task.id)}
              className="flex items-center gap-2 rounded-lg border border-warm/40 bg-warm/12 px-3.5 py-2 text-[12.5px] font-bold text-warm transition-all hover:-translate-y-px hover:bg-warm/20"
            >
              <IcRetry className="h-4 w-4" /> Повторить
            </button>
          )}
          {task.status === "done" && (
            <button
              onClick={() => {
                onDownload(task, "транскрипт.txt");
                setTimeout(() => onDownload(task, "субтитры.srt"), 350);
                setTimeout(() => onDownload(task, "сводка.json"), 700);
              }}
              className="flex items-center gap-2 rounded-lg border border-acc/40 bg-acc/12 px-3.5 py-2 text-[12.5px] font-bold text-acc transition-all hover:-translate-y-px hover:bg-acc/20"
            >
              <IcDownload className="h-4 w-4" /> Скачать всё
            </button>
          )}
          <button
            onClick={() => onDelete(task.id)}
            className="ml-auto flex items-center gap-2 rounded-lg border border-ink-600/70 px-3.5 py-2 text-[12.5px] font-bold text-fog-400 transition-all hover:border-coral/40 hover:bg-coral/10 hover:text-coral"
          >
            <IcTrash className="h-4 w-4" /> Удалить
          </button>
        </footer>
      </aside>
    </div>
  );
}
