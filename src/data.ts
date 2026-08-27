import type { LogLine, Task, TranscriptSegment } from "./types";

/* ---------------- deterministic random ---------------- */

export function mulberry32(seed: number) {
  let a = seed >>> 0;
  return () => {
    a |= 0;
    a = (a + 0x6d2b79f5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

export function seedFromId(id: string) {
  let h = 2166136261;
  for (let i = 0; i < id.length; i++) {
    h ^= id.charCodeAt(i);
    h = Math.imul(h, 16777619);
  }
  return h >>> 0;
}

/* ---------------- formatting ---------------- */

const p2 = (n: number) => String(Math.floor(n)).padStart(2, "0");

export function fmtDur(sec: number) {
  const s = Math.max(0, Math.floor(sec));
  const h = Math.floor(s / 3600);
  const m = Math.floor((s % 3600) / 60);
  const r = s % 60;
  return h > 0 ? `${h}:${p2(m)}:${p2(r)}` : `${p2(m)}:${p2(r)}`;
}

export function fmtDurLong(sec: number) {
  const m = Math.round(sec / 60);
  if (m < 60) return `${m} мин`;
  return `${Math.floor(m / 60)} ч ${m % 60} мин`;
}

export function fmtClock(ts: number) {
  const d = new Date(ts);
  return `${p2(d.getHours())}:${p2(d.getMinutes())}:${p2(d.getSeconds())}`;
}

export function fmtDay(ts: number) {
  const d = new Date(ts);
  const now = new Date();
  const sameDay = d.toDateString() === now.toDateString();
  const yest = new Date(now.getTime() - 86400000).toDateString() === d.toDateString();
  const time = `${p2(d.getHours())}:${p2(d.getMinutes())}`;
  if (sameDay) return `сегодня ${time}`;
  if (yest) return `вчера ${time}`;
  return `${new Intl.DateTimeFormat("ru-RU", { day: "numeric", month: "short" }).format(d)} ${time}`;
}

export function fmtSize(mb: number) {
  return mb >= 1024 ? `${(mb / 1024).toFixed(2)} ГБ` : `${mb.toFixed(1)} МБ`;
}

export const fmtNum = new Intl.NumberFormat("ru-RU");

export function fmtSrtTime(sec: number) {
  const s = Math.floor(sec);
  const ms = Math.round((sec - s) * 1000);
  return `${p2(Math.floor(s / 3600))}:${p2(Math.floor((s % 3600) / 60))}:${p2(s % 60)},${String(ms).padStart(3, "0")}`;
}

/* ---------------- status meta ---------------- */

export const STATUS_META: Record<
  Task["status"],
  { label: string; text: string; chip: string; dot: string; bar: string }
> = {
  pending: {
    label: "В очереди",
    text: "text-fog-300",
    chip: "bg-ink-700/70 border-fog-500/25 text-fog-300",
    dot: "bg-fog-400",
    bar: "bg-fog-400",
  },
  running: {
    label: "Выполняется",
    text: "text-warm",
    chip: "bg-warm/10 border-warm/35 text-warm",
    dot: "bg-warm pulse-dot",
    bar: "bg-warm",
  },
  done: {
    label: "Завершено",
    text: "text-mint",
    chip: "bg-mint/10 border-mint/30 text-mint",
    dot: "bg-mint",
    bar: "bg-mint",
  },
  error: {
    label: "Ошибка",
    text: "text-coral",
    chip: "bg-coral/10 border-coral/35 text-coral",
    dot: "bg-coral",
    bar: "bg-coral",
  },
};

export const MODELS = ["whisper-large-v3", "whisper-medium", "whisper-base", "parakeet-tdt-0.6b"];
export const LANGS = ["Русский", "English", "Deutsch", "Español", "Türkçe", "中文"];

/* ---------------- log generators ---------------- */

export function bootLog(fileName: string, model: string): LogLine[] {
  const t = Date.now();
  return [
    { t, text: `$ python scripts/transcribe.py --input media/uploads/${fileName} --output media/results/`, level: "info" },
    { t: t + 400, text: "[env] torch 2.3.1 · CUDA 12.4 · GPU NVIDIA A10G (22.4 ГБ)", level: "info" },
    { t: t + 900, text: `[model] загрузка весов ${model} … OK (2.9 c)`, level: "info" },
    { t: t + 1400, text: "[ffmpeg] извлечение аудиодорожки: 44 100 Гц, stereo → mono 16 кГц", level: "info" },
    { t: t + 2000, text: "[vad] детекция речи:Silero VAD, порог 0.35", level: "info" },
  ];
}

const RUN_LINES = [
  "[decode] beam=5, temperature=0.0, best_of=5",
  "[gpu] VRAM занято 14.8 / 22.4 ГБ · утилизация 96%",
  "[chunk] обработан фрагмент #{n} из {total}",
  "[align] forced alignment: уточнение таймкодов",
  "[diarize] спектральное разделение спикеров",
  "[decode] подавление галлюцинаций: no_speech_prob < 0.40",
  "[chunk] пропуск тишины {skip} c",
  "[decode] language=ru (p=0.993)",
  "[cache] KV-кэш сегмента сохранён",
  "[chunk] скорость 1.8× реального времени",
];

export function runLogLine(progress: number, durationSec: number): LogLine {
  const tmpl = RUN_LINES[Math.floor(Math.random() * RUN_LINES.length)];
  const total = Math.max(8, Math.round(durationSec / 24));
  const text = tmpl
    .replace("{n}", String(Math.max(1, Math.round((progress / 100) * total))))
    .replace("{total}", String(total))
    .replace("{skip}", String(Math.round(3 + Math.random() * 14)));
  return { t: Date.now(), text, level: "info" };
}

export function doneLog(words: number, confidence: number): LogLine[] {
  const t = Date.now();
  return [
    { t, text: `[export] слов распознано: ${fmtNum.format(words)} · CER 2.4%`, level: "ok" },
    { t: t + 300, text: "[export] записано: транскрипт.txt, субтитры.srt, сводка.json", level: "ok" },
    { t: t + 600, text: `[done] уверенность ${confidence.toFixed(1)}% · процесс завершён с кодом 0`, level: "ok" },
  ];
}

/* ---------------- transcript generator ---------------- */

const SENTENCES = [
  "Если честно, мы не ожидали такого отклика на первую версию продукта.",
  "Давай вернёмся к этому вопросу после того, как закроем текущий спринт.",
  "Основная проблема была в том, что пользователи не понимали, с чего начать.",
  "Мы провели четырнадцать глубинных интервью за последние две недели.",
  "Смотри, метрики удержания выросли на девять процентов после редизайна.",
  "Это классическая ошибка: сначала строить решение, а потом искать проблему.",
  "Я бы предложил разбить задачу на три этапа и оценить каждый отдельно.",
  "Коллеги из поддержки говорят, что половина обращений — про онбординг.",
  "Нам нужно синхронизироваться с командой аналитики до конца недели.",
  "Звук местами плывёт, но модель уверенно справляется с терминами.",
  "По данным опроса, семьдесят процентов респондентов пользуются мобильной версией.",
  "Хорошо, зафиксируем это в протоколе и вернёмся на следующем дейли.",
  "Важно не путать корреляцию с причинно-следственной связью в этих данных.",
  "Релиз запланирован на вторник, но нужен запас времени на ревью.",
  "Интересно, что пиковая нагрузка приходится на утро, а не на вечер.",
  "Да, полностью согласен — документация сейчас важнее новых функций.",
  "Мы используем скользящее окно в тридцать дней для всех когорт.",
  "Если темп сохранится, то к концу квартала закроем годовой план.",
];

const SPEAKERS = ["Спикер 1", "Спикер 2"];

export function makeTranscript(durationSec: number, seed: number, diar: boolean): TranscriptSegment[] {
  const rnd = mulberry32(seed);
  const segs: TranscriptSegment[] = [];
  let t = 0.8 + rnd() * 2;
  let i = 0;
  let sp = 0;
  while (t < durationSec - 6 && segs.length < 120) {
    const len = 4 + rnd() * 6.5;
    const end = Math.min(durationSec - 0.4, t + len);
    if (diar && rnd() < 0.68) sp = 1 - sp;
    segs.push({
      start: t,
      end,
      speaker: diar ? SPEAKERS[sp] : "Спикер 1",
      text: SENTENCES[i % SENTENCES.length],
    });
    i++;
    t = end + 0.5 + rnd() * 3.2;
  }
  return segs;
}

/* ---------------- seed tasks ---------------- */

const MIN = 60;
const HOUR = 3600;
const NOW = Date.now();

function doneTask(
  id: string,
  fileName: string,
  sizeMb: number,
  durationSec: number,
  model: string,
  language: string,
  ago: number,
  diar: boolean,
): Task {
  const words = Math.round(durationSec * (2.1 + (seedFromId(id) % 5) * 0.1));
  const confidence = 93 + (seedFromId(id) % 50) / 10;
  return {
    id,
    fileName,
    sizeMb,
    durationSec,
    language,
    model,
    diarization: diar,
    status: "done",
    progress: 100,
    createdAt: NOW - ago,
    finishedAt: NOW - ago + durationSec * 900,
    log: [
      ...bootLog(fileName, model),
      { t: NOW - ago + 8000, text: "[decode] обработка завершена без замечаний", level: "info" },
      ...doneLog(words, confidence),
    ],
    transcript: makeTranscript(durationSec, seedFromId(id), diar),
    words,
    confidence,
    speakers: diar ? 2 : 1,
  };
}

export function seedTasks(): Task[] {
  return [
    {
      id: "tsk-1041",
      fileName: "презентация_Q1_стратегия.mp3",
      sizeMb: 44.2,
      durationSec: 46 * MIN,
      language: "Русский",
      model: "whisper-large-v3",
      diarization: true,
      status: "running",
      progress: 38,
      createdAt: NOW - 11 * MIN,
      log: [
        ...bootLog("презентация_Q1_стратегия.mp3", "whisper-large-v3"),
        { t: NOW - 9 * MIN, text: "[decode] beam=5, temperature=0.0, best_of=5", level: "info" },
        { t: NOW - 7 * MIN, text: "[chunk] обработан фрагмент #18 из 115", level: "info" },
        { t: NOW - 4 * MIN, text: "[gpu] VRAM занято 15.1 / 22.4 ГБ · утилизация 97%", level: "info" },
      ],
    },
    {
      id: "tsk-1040",
      fileName: "интервью_с_дизайнером.wav",
      sizeMb: 288.4,
      durationSec: 29 * MIN,
      language: "Русский",
      model: "whisper-medium",
      diarization: true,
      status: "pending",
      progress: 0,
      createdAt: NOW - 4 * MIN,
      log: [{ t: NOW - 4 * MIN, text: "Задача поставлена в очередь · позиция 2", level: "info" }],
    },
    doneTask("tsk-1039", "интервью_о_продукте.wav", 312.8, 34 * MIN, "whisper-large-v3", "Русский", 2 * HOUR, true),
    doneTask("tsk-1038", "дейли_команды_14_02.m4a", 11.6, 12 * MIN, "whisper-base", "Русский", 5 * HOUR, false),
    {
      id: "tsk-1037",
      fileName: "интервью_hr_кандидат.mp3",
      sizeMb: 61.0,
      durationSec: 52 * MIN,
      language: "Русский",
      model: "whisper-large-v3",
      diarization: true,
      status: "error",
      progress: 63,
      createdAt: NOW - 7 * HOUR,
      error: "CUDA out of memory: не удалось выделить 6.2 ГиБ (свободно 3.1 ГиБ). Процесс прерван на 63%.",
      log: [
        ...bootLog("интервью_hr_кандидат.mp3", "whisper-large-v3"),
        { t: NOW - 7 * HOUR + 40000, text: "[gpu] VRAM занято 21.9 / 22.4 ГБ · утилизация 100%", level: "warn" },
        { t: NOW - 7 * HOUR + 96000, text: "RuntimeError: CUDA out of memory (6.2 ГиБ)", level: "err" },
        { t: NOW - 7 * HOUR + 96500, text: "[exit] процесс завершён с кодом 1", level: "err" },
      ],
    },
    doneTask("tsk-1036", "подкаст_ep47_монтаж.mp3", 84.3, 58 * MIN, "whisper-large-v3", "Русский", 11 * HOUR, true),
    doneTask("tsk-1035", "звонок_клиент_акме.wav", 190.2, 21 * MIN, "whisper-medium", "Русский", 26 * HOUR, true),
    doneTask("tsk-1034", "созвон_с_саппортом.m4a", 15.9, 17 * MIN, "whisper-base", "Русский", 30 * HOUR, false),
    doneTask("tsk-1033", "вебинар_onboarding.mp3", 96.7, 63 * MIN, "parakeet-tdt-0.6b", "English", 2 * 24 * HOUR, true),
    doneTask("tsk-1032", "лекция_матан_поток.mp3", 78.5, 84 * MIN, "whisper-medium", "Русский", 3 * 24 * HOUR, false),
  ];
}

/* ---------------- chart data ---------------- */

export const ACTIVITY_24H = [
  12, 8, 5, 3, 4, 9, 18, 32, 41, 38, 45, 52, 47, 39, 55, 61, 58, 44, 37, 29, 22, 19, 16, 13,
];

/* ---------------- result files ---------------- */

export function resultFiles(task: Task): { name: string; size: string }[] {
  const kb = Math.max(4, Math.round(task.durationSec * 0.13));
  return [
    { name: "транскрипт.txt", size: `${kb} КБ` },
    { name: "субтитры.srt", size: `${Math.round(kb * 1.6)} КБ` },
    { name: "сводка.json", size: "2 КБ" },
  ];
}

export function buildTxt(task: Task): string {
  if (!task.transcript) return "";
  return task.transcript
    .map((s) => `[${fmtDur(s.start)}] ${s.speaker}: ${s.text}`)
    .join("\n");
}

export function buildSrt(task: Task): string {
  if (!task.transcript) return "";
  return task.transcript
    .map((s, i) => `${i + 1}\n${fmtSrtTime(s.start)} --> ${fmtSrtTime(s.end)}\n${s.text}\n`)
    .join("\n");
}

export function buildSummary(task: Task): string {
  return JSON.stringify(
    {
      task_id: task.id,
      file: task.fileName,
      model: task.model,
      language: task.language,
      duration_sec: task.durationSec,
      words: task.words ?? null,
      confidence: task.confidence ?? null,
      speakers: task.speakers ?? 1,
      created_at: new Date(task.createdAt).toISOString(),
      finished_at: task.finishedAt ? new Date(task.finishedAt).toISOString() : null,
    },
    null,
    2,
  );
}

export function downloadBlob(content: string, name: string, mime = "text/plain;charset=utf-8") {
  const blob = new Blob(["\uFEFF" + content], { type: mime });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = name;
  document.body.appendChild(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 4000);
}
