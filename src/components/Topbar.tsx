import { useEffect, useState } from "react";
import type { ViewId } from "../types";
import { IcBell, IcSearch, IcUpload, IcClose } from "../icons";

function LiveClock() {
  const [now, setNow] = useState(() => new Date());
  useEffect(() => {
    const id = setInterval(() => setNow(new Date()), 1000);
    return () => clearInterval(id);
  }, []);
  const p2 = (n: number) => String(n).padStart(2, "0");
  return (
    <div className="hidden items-baseline gap-2 lg:flex" aria-label="Текущее время">
      <span className="font-mono text-[15px] font-semibold tabular-nums text-snow">
        {p2(now.getHours())}:{p2(now.getMinutes())}
        <span className="text-fog-500">:{p2(now.getSeconds())}</span>
      </span>
      <span className="font-mono text-[10px] uppercase tracking-[0.16em] text-fog-500">
        {new Intl.DateTimeFormat("ru-RU", { weekday: "short", day: "numeric", month: "short" }).format(now)}
      </span>
    </div>
  );
}

export default function Topbar({
  view,
  search,
  onSearch,
  onNewTask,
  onBell,
}: {
  view: ViewId;
  search: string;
  onSearch: (v: string) => void;
  onNewTask: () => void;
  onBell: () => void;
}) {
  const meta: Record<ViewId, { title: string; sub: string }> = {
    overview: { title: "Обзор", sub: "состояние сервиса в реальном времени" },
    tasks: { title: "Задачи", sub: "транскрибация, логи и результаты" },
  };

  return (
    <header className="sticky top-0 z-20 border-b border-ink-700/60 bg-ink-950/75 backdrop-blur-xl">
      <div className="flex items-center gap-4 px-4 py-3.5 md:px-7">
        <div className="mr-auto min-w-0">
          <h1 className="font-display text-[17px] font-bold leading-tight tracking-tight text-snow md:text-lg">
            {meta[view].title}
          </h1>
          <p className="mt-0.5 hidden truncate text-xs text-fog-500 sm:block">{meta[view].sub}</p>
        </div>

        <div className="relative hidden w-[240px] xl:w-[300px] sm:block">
          <IcSearch className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-fog-500" />
          <input
            value={search}
            onChange={(e) => onSearch(e.target.value)}
            placeholder="Поиск по файлам и моделям…"
            className="w-full rounded-lg border border-ink-600/70 bg-ink-850/80 py-2 pl-9 pr-8 text-[13px] text-snow placeholder-fog-500 outline-none transition-all duration-200 focus:border-acc/50 focus:bg-ink-800 focus:shadow-[0_0_0_3px_rgba(44,217,200,0.12)]"
          />
          {search && (
            <button
              onClick={() => onSearch("")}
              className="absolute right-2 top-1/2 -translate-y-1/2 rounded p-1 text-fog-500 transition hover:text-snow"
              aria-label="Очистить поиск"
            >
              <IcClose className="h-3.5 w-3.5" />
            </button>
          )}
        </div>

        <LiveClock />

        <button
          className="relative hidden rounded-lg p-2 text-fog-400 transition hover:bg-ink-800 hover:text-snow xl:block"
          aria-label="Уведомления"
          onClick={onBell}
        >
          <IcBell className="h-[18px] w-[18px]" />
          <span className="absolute right-1.5 top-1.5 h-1.5 w-1.5 rounded-full bg-coral" />
        </button>

        <button
          onClick={onNewTask}
          className="sweep group relative flex items-center gap-2 overflow-hidden rounded-lg border border-acc/40 bg-acc/12 px-3.5 py-2 text-[13px] font-bold text-acc transition-all duration-200 hover:-translate-y-px hover:border-acc/70 hover:bg-acc/20 hover:shadow-[0_8px_24px_-8px_rgba(44,217,200,0.45)] active:translate-y-0"
        >
          <IcUpload className="h-4 w-4 transition-transform duration-300 group-hover:-translate-y-0.5" />
          <span className="hidden sm:inline">Новая транскрибация</span>
          <span className="sm:hidden">Файл</span>
        </button>
      </div>
    </header>
  );
}
