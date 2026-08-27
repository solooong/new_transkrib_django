import type { Task, ViewId } from "../types";
import { LogoMark, IcGrid, IcTasks } from "../icons";

const NAV: { id: ViewId; label: string; icon: typeof IcGrid }[] = [
  { id: "overview", label: "Обзор", icon: IcGrid },
  { id: "tasks", label: "Задачи", icon: IcTasks },
];

export default function Sidebar({
  view,
  onNavigate,
  tasks,
}: {
  view: ViewId;
  onNavigate: (v: ViewId) => void;
  tasks: Task[];
}) {
  const running = tasks.filter((t) => t.status === "running");
  const pending = tasks.filter((t) => t.status === "pending").length;

  return (
    <aside className="fixed inset-y-0 left-0 z-30 flex w-[68px] flex-col border-r border-ink-700/60 bg-ink-900/80 backdrop-blur-xl md:w-[230px]">
      {/* логотип */}
      <div className="flex items-center gap-3 px-3.5 pb-6 pt-5 md:px-5">
        <LogoMark className="h-9 w-9 shrink-0" />
        <div className="hidden md:block">
          <p className="font-display text-[15px] font-bold leading-none tracking-tight text-snow">
            ТРАНСКРИБ
          </p>
          <p className="mt-1.5 font-mono text-[10px] uppercase tracking-[0.18em] text-fog-500">
            speech → text
          </p>
        </div>
      </div>

      {/* навигация */}
      <nav className="px-2.5 md:px-3">
        <p className="mb-2 hidden px-2 font-mono text-[10px] uppercase tracking-[0.2em] text-fog-500 md:block">
          Разделы
        </p>
        {NAV.map((item) => {
          const active = view === item.id;
          const Icon = item.icon;
          return (
            <button
              key={item.id}
              onClick={() => onNavigate(item.id)}
              className={`group relative mb-1 flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-[13.5px] font-semibold transition-all duration-200 ${
                active
                  ? "bg-ink-700/80 text-snow shadow-[inset_0_1px_0_rgba(255,255,255,0.05)]"
                  : "text-fog-400 hover:bg-ink-800 hover:text-snow"
              }`}
            >
              <span
                className={`absolute left-0 top-1/2 h-5 w-[3px] -translate-y-1/2 rounded-r-full bg-acc transition-all duration-300 ${
                  active ? "opacity-100" : "opacity-0 group-hover:opacity-40"
                }`}
              />
              <Icon className={`h-[18px] w-[18px] shrink-0 transition-colors ${active ? "text-acc" : ""}`} />
              <span className="hidden md:inline">{item.label}</span>
              {item.id === "tasks" && pending > 0 && (
                <span className="ml-auto hidden rounded-md bg-ink-600/80 px-1.5 py-0.5 font-mono text-[10px] font-semibold text-fog-300 md:inline">
                  {pending + running.length}
                </span>
              )}
            </button>
          );
        })}
      </nav>

      {/* живая очередь */}
      <div className="mt-7 hidden flex-1 overflow-hidden px-3 md:block">
        <p className="mb-2 px-2 font-mono text-[10px] uppercase tracking-[0.2em] text-fog-500">
          В работе
        </p>
        {running.length === 0 ? (
          <p className="px-2 text-xs leading-relaxed text-fog-500">
            GPU свободен — очередь пуста
          </p>
        ) : (
          <div className="space-y-2">
            {running.slice(0, 3).map((t) => (
              <div
                key={t.id}
                className="rounded-lg border border-ink-700/70 bg-ink-850/80 p-2.5 transition-colors hover:border-warm/30"
              >
                <div className="flex items-center gap-2">
                  <span className="h-1.5 w-1.5 shrink-0 rounded-full bg-warm pulse-dot" />
                  <p className="truncate font-mono text-[11px] text-fog-300">{t.fileName}</p>
                </div>
                <div className="mt-2 flex items-center gap-2">
                  <div className="h-1 flex-1 overflow-hidden rounded-full bg-ink-600/70">
                    <div
                      className="h-full rounded-full bg-warm transition-all duration-700"
                      style={{ width: `${t.progress}%` }}
                    />
                  </div>
                  <span className="font-mono text-[10px] font-semibold text-warm">
                    {Math.floor(t.progress)}%
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* низ: статус + пользователь */}
      <div className="mt-auto border-t border-ink-700/60 p-3 md:p-4">
        <div className="mb-3 hidden items-center gap-2 rounded-lg bg-ink-850/70 px-3 py-2 md:flex">
          <span className="h-2 w-2 rounded-full bg-mint shadow-[0_0_8px_rgba(65,211,147,0.7)]" />
          <span className="text-[11.5px] font-semibold text-fog-300">GPU A10G · онлайн</span>
          <span className="ml-auto font-mono text-[10px] text-fog-500">v2.4.1</span>
        </div>
        <div className="flex items-center gap-2.5">
          <span className="grid h-8 w-8 shrink-0 place-items-center rounded-full border border-acc/35 bg-acc/12 font-display text-[11px] font-bold text-acc">
            АК
          </span>
          <div className="hidden min-w-0 md:block">
            <p className="truncate text-[12.5px] font-bold text-snow">Аня Ковалёва</p>
            <p className="truncate font-mono text-[10px] text-fog-500">tariff: studio</p>
          </div>
        </div>
      </div>
    </aside>
  );
}
