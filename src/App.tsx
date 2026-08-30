import { useCallback, useEffect, useRef, useState } from "react";
import type { EventItem, Task, ToastItem, ViewId } from "./types";
import {
  bootLog,
  buildSrt,
  buildSummary,
  buildTxt,
  doneLog,
  downloadBlob,
  fmtClock,
  fmtNum,
  makeTranscript,
  runLogLine,
  seedFromId,
  seedTasks,
  STATUS_META,
} from "./data";
import Sidebar from "./components/Sidebar";
import Topbar from "./components/Topbar";
import StatsBand from "./components/StatsBand";
import RunnerPanel from "./components/RunnerPanel";
import TasksTable from "./components/TasksTable";
import TaskDrawer from "./components/TaskDrawer";
import NewTaskModal, { type NewTaskPayload } from "./components/NewTaskModal";
import Toasts from "./components/Toasts";
import Reveal from "./components/Reveal";
import { IcArrowUpRight, IcChevronR, IcWave } from "./icons";

/* ================= фоновые слои ================= */

function Ambient() {
  const wave =
    "M0,150 Q50,80 100,150 T200,150 T300,150 T400,150 T500,150 T600,150 T700,150 T800,150 T900,150 T1000,150 T1100,150 T1200,150 T1300,150 T1400,150 T1500,150 T1600,150 T1700,150 T1800,150 T1900,150 T2000,150 T2100,150 T2200,150 T2300,150 T2400,150";
  return (
    <div className="pointer-events-none fixed inset-0 z-0 overflow-hidden" aria-hidden>
      <div
        className="absolute inset-0"
        style={{
          backgroundImage:
            "linear-gradient(rgba(120,140,175,0.055) 1px, transparent 1px), linear-gradient(90deg, rgba(120,140,175,0.055) 1px, transparent 1px)",
          backgroundSize: "56px 56px",
          maskImage: "radial-gradient(ellipse 90% 65% at 50% 0%, black, transparent 78%)",
          WebkitMaskImage: "radial-gradient(ellipse 90% 65% at 50% 0%, black, transparent 78%)",
        }}
      />
      <div
        className="absolute -left-28 -top-36 h-[500px] w-[500px] rounded-full blur-[130px]"
        style={{ background: "rgba(44,217,200,0.10)" }}
      />
      <div
        className="absolute -bottom-44 -right-28 h-[540px] w-[540px] rounded-full blur-[140px]"
        style={{ background: "rgba(242,163,60,0.08)" }}
      />
      <div
        className="absolute right-[12%] top-[30%] h-[300px] w-[300px] rounded-full blur-[120px]"
        style={{ background: "rgba(107,147,240,0.07)" }}
      />
      <svg className="bg-drift absolute bottom-6 left-0 w-[200%] opacity-[0.055]" viewBox="0 0 2400 300" fill="none">
        <path d={wave} stroke="#2CD9C8" strokeWidth="2" />
        <path d={wave} stroke="#F2A33C" strokeWidth="1.5" transform="translate(40,26)" />
        <path d={wave} stroke="#6B93F0" strokeWidth="1.5" transform="translate(-60,-30)" />
      </svg>
      <div className="noise" />
    </div>
  );
}

/* ================= лента событий ================= */

const EVENT_DOT: Record<EventItem["kind"], string> = {
  start: "bg-acc",
  done: "bg-mint",
  error: "bg-coral",
  queue: "bg-fog-400",
  retry: "bg-warm",
};

function EventFeed({ events }: { events: EventItem[] }) {
  return (
    <section className="panel panel-hairline flex h-full flex-col p-5" aria-label="Лента событий">
      <header className="mb-3.5 flex items-center gap-2.5">
        <h2 className="font-display text-[13.5px] font-bold tracking-tight text-snow">Лента событий</h2>
        <span className="ml-auto rounded-md bg-ink-700/80 px-2 py-0.5 font-mono text-[10px] font-semibold text-fog-400">
          {events.length}
        </span>
      </header>
      <div className="min-h-0 flex-1 space-y-1 overflow-y-auto pr-1" style={{ maxHeight: 380 }}>
        {events.map((e) => (
          <div
            key={e.id}
            className="log-line flex items-start gap-2.5 rounded-lg px-2 py-2 transition-colors hover:bg-ink-800/60"
          >
            <span className={`mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full ${EVENT_DOT[e.kind]}`} />
            <div className="min-w-0 flex-1">
              <p className="text-[12.5px] font-semibold leading-snug text-fog-300">{e.text}</p>
              <p className="mt-0.5 font-mono text-[10px] text-fog-500">{fmtClock(e.t)}</p>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}

/* ================= движок ================= */

let idCounter = 5000;
const nextId = () => ++idCounter;

function engineTick(tasks: Task[]): {
  next: Task[];
  events: Omit<EventItem, "id" | "t">[];
  toasts: Omit<ToastItem, "id">[];
} {
  const events: Omit<EventItem, "id" | "t">[] = [];
  const toasts: Omit<ToastItem, "id">[] = [];
  const runningNow = tasks.filter((t) => t.status === "running").length;

  const next = tasks.map((t) => {
    if (t.status !== "running") return t;
    const speed = t.model.includes("large")
      ? 1.9
      : t.model.includes("medium")
        ? 2.8
        : t.model.includes("base")
          ? 4.4
          : 3.6;
    const p = Math.min(100, t.progress + speed * (0.6 + Math.random()));
    let log = t.log;
    if (Math.random() < 0.5 && log.length < 90) log = [...log, runLogLine(p, t.durationSec)];

    if (p >= 100) {
      const words = Math.round(t.durationSec * (2.1 + Math.random() * 0.5));
      const confidence = 93 + Math.random() * 5.2;
      events.push({ kind: "done", text: `«${t.fileName}» распознан · ${fmtNum.format(words)} слов` });
      toasts.push({ kind: "success", title: "Транскрибация завершена", text: t.fileName });
      return {
        ...t,
        status: "done" as const,
        progress: 100,
        finishedAt: Date.now(),
        log: [...log, ...doneLog(words, confidence)],
        transcript: makeTranscript(t.durationSec, seedFromId(t.id) ^ (Date.now() % 9973), t.diarization),
        words,
        confidence,
        speakers: t.diarization ? 2 : 1,
      };
    }
    return { ...t, progress: p, log };
  });

  if (runningNow < 2) {
    const idx = next.findIndex((t) => t.status === "pending");
    if (idx >= 0) {
      const t = next[idx];
      next[idx] = { ...t, status: "running", progress: 1.5, log: [...t.log, ...bootLog(t.fileName, t.model)] };
      events.push({ kind: "start", text: `GPU принял «${t.fileName}» в работу` });
    }
  }

  return { next, events, toasts };
}

/* ================= приложение ================= */

export default function App() {
  const [tasks, setTasks] = useState<Task[]>(seedTasks);
  const [view, setView] = useState<ViewId>("overview");
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<Task["status"] | "all">("all");
  const [drawerId, setDrawerId] = useState<string | null>("tsk-1041");
  const [modalOpen, setModalOpen] = useState(false);
  const [toasts, setToasts] = useState<ToastItem[]>([]);
  const [events, setEvents] = useState<EventItem[]>(() => {
    const now = Date.now();
    return [
      { id: 1, t: now - 4 * 60000, kind: "queue", text: "«интервью_с_дизайнером.wav» в очереди · позиция 2" },
      { id: 2, t: now - 10 * 60000, kind: "start", text: "GPU принял «презентация_Q1_стратегия.mp3» в работу" },
      { id: 3, t: now - 96 * 60000, kind: "done", text: "«интервью_о_продукте.wav» распознан · 4 692 слова" },
      { id: 4, t: now - 410 * 60000, kind: "error", text: "«интервью_hr_кандидат.mp3» — CUDA out of memory" },
      { id: 5, t: now - 660 * 60000, kind: "done", text: "«подкаст_ep47_монтаж.mp3» распознан · 8 114 слов" },
    ];
  });

  const tasksRef = useRef(tasks);
  useEffect(() => {
    tasksRef.current = tasks;
  }, [tasks]);

  const pushToast = useCallback((t: Omit<ToastItem, "id">) => {
    setToasts((list) => [...list.slice(-3), { ...t, id: nextId() }]);
  }, []);

  /* движок задач */
  useEffect(() => {
    const id = setInterval(() => {
      const { next, events: ev, toasts: ts } = engineTick(tasksRef.current);
      if (ev.length) {
        const stamped = ev.map((e) => ({ ...e, id: nextId(), t: Date.now() }));
        setEvents((f) => [...stamped, ...f].slice(0, 40));
      }
      ts.forEach((t) => pushToast(t));
      setTasks(next);
    }, 1100);
    return () => clearInterval(id);
  }, [pushToast]);

  /* действия */
  const createTask = (p: NewTaskPayload) => {
    const durMin = Math.max(1, Math.min(90, Math.round(p.sizeMb * 0.9)));
    const t: Task = {
      id: `tsk-${1042 + tasksRef.current.length}`,
      fileName: p.name,
      sizeMb: p.sizeMb,
      durationSec: durMin * 60 + Math.floor(Math.random() * 40),
      language: p.lang,
      model: p.model,
      diarization: p.diar,
      status: "pending",
      progress: 0,
      createdAt: Date.now(),
      log: [{ t: Date.now(), text: "Задача поставлена в очередь · ожидает GPU", level: "info" }],
    };
    setTasks((list) => [t, ...list]);
    setEvents((f) => [{ id: nextId(), t: Date.now(), kind: "queue" as const, text: `«${p.name}» в очереди на транскрибацию` }, ...f].slice(0, 40));
    pushToast({ kind: "info", title: "Задача создана", text: `${p.name} · ${p.model}` });
    setModalOpen(false);
    setView("tasks");
    setStatusFilter("all");
    setSearch("");
  };

  const retryTask = (id: string) => {
    setTasks((list) =>
      list.map((t) =>
        t.id === id
          ? {
              ...t,
              status: "running",
              progress: 2,
              error: undefined,
              log: [
                ...t.log,
                { t: Date.now(), text: "[retry] повторная попытка · лимит VRAM увеличен до 20 ГБ", level: "warn" },
                ...bootLog(t.fileName, t.model),
              ],
            }
          : t,
      ),
    );
    setEvents((f) => [{ id: nextId(), t: Date.now(), kind: "retry" as const, text: `Повторный запуск «${id}»` }, ...f].slice(0, 40));
    pushToast({ kind: "info", title: "Повторная попытка запущена", text: id });
  };

  const deleteTask = (id: string) => {
    setTasks((list) => list.filter((t) => t.id !== id));
    setDrawerId((d) => (d === id ? null : d));
    pushToast({ kind: "error", title: "Задача удалена", text: id });
  };

  const downloadResult = (task: Task, name: string) => {
    if (name.endsWith(".srt")) downloadBlob(buildSrt(task), `${task.id}_${name}`, "text/plain;charset=utf-8");
    else if (name.endsWith(".json")) downloadBlob(buildSummary(task), `${task.id}_${name}`, "application/json;charset=utf-8");
    else downloadBlob(buildTxt(task), `${task.id}_${name}`, "text/plain;charset=utf-8");
  };

  /* выборки */
  const q = search.trim().toLowerCase();
  const filtered = tasks
    .filter((t) => (statusFilter === "all" ? true : t.status === statusFilter))
    .filter(
      (t) =>
        !q ||
        t.fileName.toLowerCase().includes(q) ||
        t.model.toLowerCase().includes(q) ||
        t.id.toLowerCase().includes(q) ||
        t.language.toLowerCase().includes(q),
    )
    .sort((a, b) => b.createdAt - a.createdAt);

  const recent = filtered.slice(0, 6);
  const drawerTask = drawerId ? tasks.find((t) => t.id === drawerId) ?? null : null;

  const chips: { id: Task["status"] | "all"; label: string; n: number }[] = [
    { id: "all", label: "Все", n: tasks.length },
    ...(["running", "pending", "done", "error"] as const).map((s) => ({
      id: s as Task["status"] | "all",
      label: STATUS_META[s].label,
      n: tasks.filter((t) => t.status === s).length,
    })),
  ];

  return (
    <div className="min-h-screen font-body">
      <Ambient />
      <Sidebar view={view} onNavigate={setView} tasks={tasks} />

      <div className="relative z-10 ml-[68px] md:ml-[230px]">
        <Topbar
          view={view}
          search={search}
          onSearch={setSearch}
          onNewTask={() => setModalOpen(true)}
          onBell={() =>
            pushToast({ kind: "info", title: "События — в ленте", text: "Все уведомления дублируются на панели «Обзор»" })
          }
        />

        <main className="mx-auto max-w-[1240px] space-y-5 px-4 py-6 md:px-7">
          {view === "overview" ? (
            <>
              <Reveal>
                <StatsBand tasks={tasks} />
              </Reveal>

              <div className="grid gap-5 xl:grid-cols-[1fr_320px]">
                <Reveal delay={80} className="min-w-0">
                  <RunnerPanel tasks={tasks} />
                </Reveal>
                <Reveal delay={160} className="min-w-0">
                  <EventFeed events={events} />
                </Reveal>
              </div>

              <Reveal delay={120}>
                <section className="panel panel-hairline overflow-hidden" aria-label="Последние задачи">
                  <header className="flex items-center gap-3 px-5 pb-1 pt-4">
                    <h2 className="font-display text-[13.5px] font-bold tracking-tight text-snow">Последние задачи</h2>
                    <span className="rounded-md bg-ink-700/80 px-2 py-0.5 font-mono text-[10px] font-semibold text-fog-400">
                      {filtered.length}
                    </span>
                    <button
                      onClick={() => setView("tasks")}
                      className="group ml-auto flex items-center gap-1 font-mono text-[11px] font-semibold text-acc transition hover:text-[#4ae6d6]"
                    >
                      все задачи
                      <IcArrowUpRight className="h-3.5 w-3.5 transition-transform duration-200 group-hover:-translate-y-0.5 group-hover:translate-x-0.5" />
                    </button>
                  </header>
                  <TasksTable tasks={recent} onOpen={(t) => setDrawerId(t.id)} compact />
                </section>
              </Reveal>
            </>
          ) : (
            <Reveal>
              <section className="panel panel-hairline overflow-hidden" aria-label="Все задачи">
                <header className="flex flex-wrap items-center gap-2 px-5 pb-3 pt-4">
                  {chips.map((c) => {
                    const active = statusFilter === c.id;
                    const tone =
                      c.id === "all"
                        ? active
                          ? "border-acc/50 bg-acc/12 text-acc"
                          : ""
                        : active
                          ? STATUS_META[c.id as Task["status"]].chip
                          : "";
                    return (
                      <button
                        key={c.id}
                        onClick={() => setStatusFilter(c.id)}
                        className={`flex items-center gap-1.5 rounded-lg border px-3 py-1.5 text-[12px] font-bold transition-all duration-200 ${
                          active
                            ? tone
                            : "border-ink-600/70 bg-ink-850/60 text-fog-400 hover:border-ink-600 hover:text-snow"
                        }`}
                      >
                        {c.label}
                        <span className={`font-mono text-[10.5px] ${active ? "opacity-80" : "text-fog-500"}`}>{c.n}</span>
                      </button>
                    );
                  })}
                  <p className="ml-auto font-mono text-[10.5px] text-fog-500">
                    показано {filtered.length} из {tasks.length}
                  </p>
                </header>

                {filtered.length > 0 ? (
                  <TasksTable tasks={filtered} onOpen={(t) => setDrawerId(t.id)} />
                ) : (
                  <div className="anim-fade-up flex flex-col items-center px-6 py-16 text-center">
                    <span className="grid h-14 w-14 place-items-center rounded-2xl border border-ink-600/70 bg-ink-800/70 text-fog-500">
                      <IcWave className="h-6 w-6" />
                    </span>
                    <p className="mt-4 font-display text-[15px] font-bold text-snow">Ничего не нашлось</p>
                    <p className="mt-1.5 max-w-[300px] text-[13px] leading-relaxed text-fog-500">
                      По запросу {q ? `«${search}»` : "выбранному фильтру"} нет ни одной задачи. Попробуйте сбросить условия.
                    </p>
                    <button
                      onClick={() => {
                        setSearch("");
                        setStatusFilter("all");
                      }}
                      className="mt-5 flex items-center gap-1.5 rounded-lg border border-acc/40 bg-acc/10 px-4 py-2 text-[12.5px] font-bold text-acc transition hover:bg-acc/20"
                    >
                      Сбросить фильтры <IcChevronR className="h-3.5 w-3.5" />
                    </button>
                  </div>
                )}
              </section>
            </Reveal>
          )}

          <footer className="flex items-center gap-3 pb-4 pt-2 font-mono text-[10.5px] text-fog-500">
            <span className="h-1 w-1 rounded-full bg-ink-600" />
            transkrib_django · панель управления v2.4.1
            <span className="ml-auto hidden sm:inline">django 5.0 · celery-free · docker compose</span>
          </footer>
        </main>
      </div>

      {drawerTask && (
        <TaskDrawer
          key={drawerTask.id}
          task={drawerTask}
          onClose={() => setDrawerId(null)}
          onRetry={retryTask}
          onDelete={deleteTask}
          onDownload={downloadResult}
        />
      )}

      {modalOpen && <NewTaskModal onClose={() => setModalOpen(false)} onCreate={createTask} />}

      <Toasts items={toasts} onClose={(id) => setToasts((l) => l.filter((t) => t.id !== id))} />
    </div>
  );
}
