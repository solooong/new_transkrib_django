import type { Task } from "../types";
import { fmtNum } from "../data";

function Spark({ points, stroke }: { points: number[]; stroke: string }) {
  const w = 76;
  const h = 26;
  const max = Math.max(...points);
  const min = Math.min(...points);
  const d = points
    .map((v, i) => {
      const x = (i / (points.length - 1)) * w;
      const y = h - 3 - ((v - min) / (max - min || 1)) * (h - 6);
      return `${i ? "L" : "M"}${x.toFixed(1)},${y.toFixed(1)}`;
    })
    .join(" ");
  return (
    <svg viewBox={`0 0 ${w} ${h}`} className="h-[26px] w-[76px]" aria-hidden>
      <path d={d} fill="none" stroke={stroke} strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" opacity="0.9" />
      <circle cx={w} cy={h - 3 - ((points[points.length - 1] - min) / (max - min || 1)) * (h - 6)} r="2.4" fill={stroke} />
    </svg>
  );
}

export default function StatsBand({ tasks }: { tasks: Task[] }) {
  const day = 24 * 3600 * 1000;
  const cutoff = Date.now() - day;

  const doneToday = tasks.filter((t) => t.status === "done" && (t.finishedAt ?? t.createdAt) > cutoff);
  const minutesToday = 268 + Math.round(doneToday.reduce((s, t) => s + t.durationSec, 0) / 60);
  const avgConf =
    tasks.filter((t) => t.confidence).reduce((s, t) => s + (t.confidence ?? 0), 0) /
    Math.max(1, tasks.filter((t) => t.confidence).length);
  const inQueue = tasks.filter((t) => t.status === "pending" || t.status === "running").length;
  const createdToday = tasks.filter((t) => t.createdAt > cutoff).length;

  const stats = [
    {
      label: "Задач за 24 часа",
      value: fmtNum.format(9 + createdToday),
      note: "+3 к вчера",
      noteTone: "text-mint",
      spark: [4, 6, 5, 8, 7, 9, 11, 10, 13, 12, 14, 9 + createdToday] as number[],
      color: "#2CD9C8",
    },
    {
      label: "Минут распознано",
      value: fmtNum.format(minutesToday),
      note: `${fmtNum.format(Math.round(minutesToday * 2.4))} слов`,
      noteTone: "text-fog-500",
      spark: [18, 22, 19, 31, 28, 34, 40, 36, 44, 49, 46, minutesToday / 8] as number[],
      color: "#6B93F0",
    },
    {
      label: "Средняя точность",
      value: `${avgConf.toFixed(1)}%`,
      note: "CER 2.4%",
      noteTone: "text-fog-500",
      spark: [93, 94, 93.6, 95, 94.8, 95.6, 96, 95.4, 96.2, 96.5, 96.1, avgConf] as number[],
      color: "#41D393",
    },
    {
      label: "Сейчас в работе",
      value: String(inQueue),
      note: inQueue > 0 ? "GPU загружен" : "очередь пуста",
      noteTone: inQueue > 0 ? "text-warm" : "text-fog-500",
      spark: null,
      color: "#F2A33C",
      live: true,
    },
  ];

  return (
    <section className="panel panel-hairline grid grid-cols-2 overflow-hidden lg:grid-cols-4" aria-label="Ключевые показатели">
      {stats.map((s, i) => (
        <div
          key={s.label}
          className={`group relative px-5 py-5 transition-colors duration-300 hover:bg-ink-800/50 ${
            i > 0 ? "border-l border-ink-700/50 max-lg:[&:nth-child(3)]:border-l-0" : ""
          } ${i >= 2 ? "max-lg:border-t max-lg:border-ink-700/50" : ""}`}
        >
          <p className="font-mono text-[10px] uppercase tracking-[0.18em] text-fog-500">{s.label}</p>
          <div className="mt-2 flex items-end justify-between gap-2">
            <p className="font-display text-[26px] font-bold leading-none tracking-tight text-snow transition-transform duration-300 group-hover:-translate-y-0.5">
              {s.value}
              {s.live && (
                <span className="ml-2 inline-block h-2 w-2 -translate-y-1 rounded-full bg-warm pulse-dot" />
              )}
            </p>
            {s.spark ? <Spark points={s.spark} stroke={s.color} /> : (
              <span className={`mb-0.5 font-mono text-[10px] ${s.noteTone}`}>live</span>
            )}
          </div>
          <p className={`mt-1.5 text-[11.5px] font-semibold ${s.noteTone}`}>{s.note}</p>
        </div>
      ))}
    </section>
  );
}
