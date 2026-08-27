import { useState } from "react";
import type { SystemMetrics, Task } from "../types";
import { ACTIVITY_24H, STATUS_META, fmtNum } from "../data";

/* ---------- полукруглый датчик ---------- */

function Gauge({ label, value, unit = "%" }: { label: string; value: number; unit?: string }) {
  const C = Math.PI * 50;
  const v = Math.max(0, Math.min(100, value));
  const color = v < 55 ? "#41D393" : v < 80 ? "#F2A33C" : "#F26D64";
  return (
    <div className="flex flex-col items-center rounded-xl border border-ink-700/60 bg-ink-900/50 px-2 pb-3 pt-4 transition-colors duration-300 hover:border-ink-600">
      <svg viewBox="0 0 120 68" className="w-[104px]">
        <path d="M10 62 A50 50 0 0 1 110 62" fill="none" stroke="rgba(120,140,175,0.16)" strokeWidth="8" strokeLinecap="round" />
        <path
          d="M10 62 A50 50 0 0 1 110 62"
          fill="none"
          stroke={color}
          strokeWidth="8"
          strokeLinecap="round"
          strokeDasharray={C}
          strokeDashoffset={C * (1 - v / 100)}
          className="gauge-arc"
          style={{ filter: `drop-shadow(0 0 6px ${color}55)` }}
        />
        <text x="60" y="52" textAnchor="middle" fill="#E9F0FB" fontSize="19" fontWeight="700" fontFamily="JetBrains Mono, monospace">
          {Math.round(v)}
          <tspan fontSize="10" fill="#7C8AA5">{unit}</tspan>
        </text>
      </svg>
      <p className="mt-1 font-mono text-[10px] uppercase tracking-[0.18em] text-fog-500">{label}</p>
    </div>
  );
}

/* ---------- график активности с ховером ---------- */

function ActivityChart() {
  const [hover, setHover] = useState<number | null>(null);
  const data = ACTIVITY_24H;
  const w = 640;
  const h = 190;
  const padX = 8;
  const padTop = 14;
  const padBot = 24;
  const max = Math.max(...data) * 1.18;
  const step = (w - padX * 2) / (data.length - 1);

  const pts = data.map((v, i) => [padX + i * step, h - padBot - (v / max) * (h - padTop - padBot)] as const);
  const line = pts.map(([x, y], i) => `${i ? "L" : "M"}${x.toFixed(1)},${y.toFixed(1)}`).join(" ");
  const area = `${line} L${pts[pts.length - 1][0]},${h - padBot} L${pts[0][0]},${h - padBot} Z`;

  const onMove = (e: React.MouseEvent<SVGSVGElement>) => {
    const r = e.currentTarget.getBoundingClientRect();
    const x = ((e.clientX - r.left) / r.width) * w;
    const idx = Math.round((x - padX) / step);
    setHover(Math.max(0, Math.min(data.length - 1, idx)));
  };

  return (
    <div className="relative h-full min-h-[190px]">
      <svg
        viewBox={`0 0 ${w} ${h}`}
        className="h-full w-full"
        onMouseMove={onMove}
        onMouseLeave={() => setHover(null)}
        role="img"
        aria-label="Минуты транскрибации по часам за сутки"
      >
        <defs>
          <linearGradient id="areaFill" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#2CD9C8" stopOpacity="0.32" />
            <stop offset="100%" stopColor="#2CD9C8" stopOpacity="0.02" />
          </linearGradient>
        </defs>
        {[0.25, 0.5, 0.75].map((f) => (
          <line
            key={f}
            x1={padX}
            x2={w - padX}
            y1={padTop + (h - padTop - padBot) * f}
            y2={padTop + (h - padTop - padBot) * f}
            stroke="rgba(120,140,175,0.12)"
            strokeDasharray="3 5"
          />
        ))}
        <path d={area} fill="url(#areaFill)" className="anim-fade" />
        <path d={line} fill="none" stroke="#2CD9C8" strokeWidth="2.2" strokeLinejoin="round" strokeLinecap="round" className="chart-line" />
        {data.map((_, i) =>
          i % 4 === 0 ? (
            <text key={i} x={padX + i * step} y={h - 7} textAnchor="middle" fontSize="9.5" fill="#7C8AA5" fontFamily="JetBrains Mono, monospace">
              {String(i).padStart(2, "0")}:00
            </text>
          ) : null,
        )}
        {hover !== null && (
          <g>
            <line x1={pts[hover][0]} x2={pts[hover][0]} y1={padTop - 4} y2={h - padBot} stroke="rgba(233,240,251,0.22)" strokeWidth="1" />
            <circle cx={pts[hover][0]} cy={pts[hover][1]} r="4.5" fill="#0D1526" stroke="#2CD9C8" strokeWidth="2.2" />
          </g>
        )}
      </svg>
      {hover !== null && (
        <div
          className="anim-fade pointer-events-none absolute -top-1 z-10 -translate-x-1/2 rounded-lg border border-ink-600 bg-ink-800 px-2.5 py-1.5 text-center shadow-xl"
          style={{ left: `${(pts[hover][0] / w) * 100}%` }}
        >
          <p className="font-mono text-[13px] font-bold leading-none text-acc">{data[hover]} мин</p>
          <p className="mt-0.5 font-mono text-[9.5px] text-fog-500">{String(hover).padStart(2, "0")}:00–{String(hover + 1).padStart(2, "0")}:00</p>
        </div>
      )}
    </div>
  );
}

/* ---------- панель ---------- */

export default function SystemMonitor({ metrics, tasks }: { metrics: SystemMetrics; tasks: Task[] }) {
  const last = (a: number[]) => a[a.length - 1] ?? 0;
  const counts = (["running", "done", "pending", "error"] as const).map((s) => ({
    s,
    n: tasks.filter((t) => t.status === s).length,
  }));
  const total = Math.max(1, tasks.length);

  return (
    <section className="panel panel-hairline p-5" aria-label="Мониторинг системы">
      <header className="mb-4 flex items-center gap-2.5">
        <span className="relative flex h-2 w-2">
          <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-mint opacity-60" />
          <span className="relative inline-flex h-2 w-2 rounded-full bg-mint" />
        </span>
        <h2 className="font-display text-[13.5px] font-bold tracking-tight text-snow">Система</h2>
        <span className="rounded-md border border-mint/25 bg-mint/10 px-2 py-0.5 font-mono text-[10px] font-semibold uppercase tracking-wider text-mint">
          live
        </span>
        <span className="ml-auto font-mono text-[10.5px] text-fog-500">
          polling /api/metrics/ · 2 c · load {metrics.load.toFixed(2)}
        </span>
      </header>

      <div className="grid gap-4 lg:grid-cols-[280px_1fr]">
        <div className="grid grid-cols-2 gap-3">
          <Gauge label="CPU" value={last(metrics.cpu)} />
          <Gauge label="Память" value={last(metrics.ram)} />
          <Gauge label="GPU" value={metrics.gpu} />
          <Gauge label="Диск" value={metrics.disk} />
        </div>
        <div className="flex flex-col rounded-xl border border-ink-700/60 bg-ink-900/40 p-3.5">
          <div className="mb-1 flex items-baseline justify-between">
            <p className="text-[12.5px] font-bold text-fog-300">Минуты транскрибации · 24 ч</p>
            <p className="font-mono text-[11px] text-fog-500">
              Σ <span className="text-acc">{fmtNum.format(ACTIVITY_24H.reduce((a, b) => a + b, 0))}</span> мин
            </p>
          </div>
          <div className="min-h-0 flex-1">
            <ActivityChart />
          </div>
        </div>
      </div>

      {/* пайплайн задач */}
      <div className="mt-4 rounded-xl border border-ink-700/60 bg-ink-900/40 p-3.5">
        <div className="mb-2.5 flex items-center justify-between">
          <p className="text-[12.5px] font-bold text-fog-300">Пайплайн задач</p>
          <p className="font-mono text-[10.5px] text-fog-500">всего {tasks.length}</p>
        </div>
        <div className="flex h-3 overflow-hidden rounded-full bg-ink-700/70">
          {counts.map(({ s, n }) =>
            n > 0 ? (
              <div
                key={s}
                className={`${STATUS_META[s].bar} transition-all duration-700 ${s === "running" ? "stripes-anim" : ""}`}
                style={{ width: `${(n / total) * 100}%`, opacity: 0.85 }}
                title={`${STATUS_META[s].label}: ${n}`}
              />
            ) : null,
          )}
        </div>
        <div className="mt-2.5 flex flex-wrap gap-x-4 gap-y-1">
          {counts.map(({ s, n }) => (
            <span key={s} className="flex items-center gap-1.5 text-[11px] font-semibold text-fog-400">
              <span className={`h-1.5 w-1.5 rounded-full ${STATUS_META[s].dot}`} />
              {STATUS_META[s].label}
              <span className="font-mono text-fog-500">{n}</span>
            </span>
          ))}
        </div>
      </div>
    </section>
  );
}
