import { useEffect, useRef, useState } from "react";
import { LANGS, MODELS, fmtSize } from "../data";
import { IcAudioFile, IcClose, IcGlobe, IcLayers, IcUpload, IcWave } from "../icons";

export interface NewTaskPayload {
  name: string;
  sizeMb: number;
  lang: string;
  model: string;
  diar: boolean;
}

export default function NewTaskModal({
  onClose,
  onCreate,
}: {
  onClose: () => void;
  onCreate: (p: NewTaskPayload) => void;
}) {
  const [file, setFile] = useState<{ name: string; sizeMb: number } | null>(null);
  const [drag, setDrag] = useState(false);
  const [lang, setLang] = useState(LANGS[0]);
  const [model, setModel] = useState(MODELS[0]);
  const [diar, setDiar] = useState(true);
  const [shake, setShake] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    const h = (e: KeyboardEvent) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", h);
    return () => window.removeEventListener("keydown", h);
  }, [onClose]);

  const pick = (f: File | undefined) => {
    if (!f) return;
    setFile({ name: f.name, sizeMb: Math.max(0.4, f.size / 1048576) });
  };

  const estMin = file ? Math.max(1, Math.min(90, Math.round(file.sizeMb * 0.9))) : 0;

  const submit = () => {
    if (!file) {
      setShake(true);
      setTimeout(() => setShake(false), 450);
      return;
    }
    onCreate({ name: file.name, sizeMb: file.sizeMb, lang, model, diar });
  };

  const selectCls =
    "w-full appearance-none rounded-lg border border-ink-600/70 bg-ink-850/80 py-2.5 pl-9 pr-8 text-[13px] font-semibold text-snow outline-none transition focus:border-acc/50 focus:shadow-[0_0_0_3px_rgba(44,217,200,0.12)]";

  return (
    <div className="fixed inset-0 z-[60] grid place-items-center p-4">
      <div className="anim-fade absolute inset-0 bg-ink-950/75 backdrop-blur-[4px]" onClick={onClose} />
      <div
        role="dialog"
        aria-modal="true"
        aria-label="Новая транскрибация"
        className={`panel anim-fade-up relative w-full max-w-[480px] overflow-hidden ${shake ? "animate-[kf-fade-up_0.4s_ease]" : ""}`}
        style={shake ? { animation: "kf-shake 0.4s ease" } : undefined}
      >
        <style>{`@keyframes kf-shake { 0%,100%{transform:translateX(0)} 25%{transform:translateX(-7px)} 50%{transform:translateX(6px)} 75%{transform:translateX(-4px)} }`}</style>

        <header className="flex items-center gap-3 border-b border-ink-700/60 px-5 py-4">
          <span className="grid h-9 w-9 place-items-center rounded-lg border border-acc/35 bg-acc/12 text-acc">
            <IcUpload className="h-[18px] w-[18px]" />
          </span>
          <div className="flex-1">
            <h2 className="font-display text-[15px] font-bold tracking-tight text-snow">Новая транскрибация</h2>
            <p className="text-[11.5px] text-fog-500">файл уйдёт в очередь на GPU-узел</p>
          </div>
          <button onClick={onClose} className="rounded-lg p-1.5 text-fog-400 transition hover:bg-ink-700 hover:text-snow" aria-label="Закрыть">
            <IcClose className="h-[18px] w-[18px]" />
          </button>
        </header>

        <div className="space-y-4 px-5 py-4">
          {/* дроп-зона */}
          <div
            onDragOver={(e) => {
              e.preventDefault();
              setDrag(true);
            }}
            onDragLeave={() => setDrag(false)}
            onDrop={(e) => {
              e.preventDefault();
              setDrag(false);
              pick(e.dataTransfer.files?.[0]);
            }}
            onClick={() => inputRef.current?.click()}
            className={`group relative cursor-pointer rounded-xl border-2 border-dashed px-5 py-6 text-center transition-all duration-300 ${
              drag
                ? "border-acc bg-acc/10 shadow-[0_0_40px_-10px_rgba(44,217,200,0.4)]"
                : file
                  ? "border-mint/50 bg-mint/6"
                  : "border-ink-600/80 bg-ink-900/50 hover:border-acc/50 hover:bg-ink-800/60"
            }`}
          >
            <input
              ref={inputRef}
              type="file"
              accept="audio/*,video/*,.mp3,.wav,.m4a,.ogg,.flac,.mp4,.mkv"
              className="hidden"
              onChange={(e) => pick(e.target.files?.[0] ?? undefined)}
            />
            {file ? (
              <div className="flex items-center gap-3 text-left">
                <span className="grid h-11 w-11 shrink-0 place-items-center rounded-lg bg-mint/15 text-mint">
                  <IcAudioFile className="h-5 w-5" />
                </span>
                <div className="min-w-0">
                  <p className="truncate text-[13.5px] font-bold text-snow">{file.name}</p>
                  <p className="mt-0.5 font-mono text-[11px] text-fog-400">
                    {fmtSize(file.sizeMb)} · оценка ~{estMin} мин аудио
                  </p>
                </div>
                <span className="ml-auto rounded-md bg-ink-700 px-2 py-1 font-mono text-[10px] font-bold uppercase text-fog-300 transition group-hover:text-acc">
                  заменить
                </span>
              </div>
            ) : (
              <>
                <IcWave className={`mx-auto h-7 w-7 transition-all duration-300 ${drag ? "scale-125 text-acc" : "text-fog-500 group-hover:text-acc"}`} />
                <p className="mt-2.5 text-[13.5px] font-bold text-snow">
                  Перетащите аудио сюда <span className="font-normal text-fog-500">или кликните</span>
                </p>
                <p className="mt-1 font-mono text-[10.5px] text-fog-500">mp3 · wav · m4a · ogg · flac · mp4 — до 2 ГБ</p>
              </>
            )}
          </div>

          <button
            onClick={() => setFile({ name: "демо_запись_митапа.wav", sizeMb: 18.4 })}
            className="mx-auto block font-mono text-[11px] text-fog-500 underline decoration-dotted underline-offset-4 transition hover:text-acc"
          >
            нет файла под рукой? взять демо-запись
          </button>

          {/* параметры */}
          <div className="grid grid-cols-2 gap-3">
            <div className="relative">
              <label className="mb-1.5 block font-mono text-[10px] uppercase tracking-[0.16em] text-fog-500">Язык</label>
              <IcGlobe className="pointer-events-none absolute bottom-[11px] left-3 h-4 w-4 text-fog-500" />
              <select value={lang} onChange={(e) => setLang(e.target.value)} className={selectCls}>
                {LANGS.map((l) => (
                  <option key={l} value={l}>{l}</option>
                ))}
              </select>
            </div>
            <div className="relative">
              <label className="mb-1.5 block font-mono text-[10px] uppercase tracking-[0.16em] text-fog-500">Модель</label>
              <IcLayers className="pointer-events-none absolute bottom-[11px] left-3 h-4 w-4 text-fog-500" />
              <select value={model} onChange={(e) => setModel(e.target.value)} className={selectCls}>
                {MODELS.map((m) => (
                  <option key={m} value={m}>{m}</option>
                ))}
              </select>
            </div>
          </div>

          <button
            onClick={() => setDiar((d) => !d)}
            className={`flex w-full items-center gap-3 rounded-lg border px-3.5 py-2.5 text-left transition-all duration-200 ${
              diar ? "border-acc/40 bg-acc/8" : "border-ink-600/70 bg-ink-900/50 hover:border-ink-600"
            }`}
            role="switch"
            aria-checked={diar}
          >
            <span
              className={`relative h-5 w-9 shrink-0 rounded-full transition-colors duration-300 ${diar ? "bg-acc" : "bg-ink-600"}`}
            >
              <span
                className={`absolute top-0.5 h-4 w-4 rounded-full bg-snow shadow transition-all duration-300 ${diar ? "left-[18px]" : "left-0.5"}`}
              />
            </span>
            <span className="min-w-0">
              <span className="block text-[13px] font-bold text-snow">Диаризация спикеров</span>
              <span className="block text-[11px] text-fog-500">разметить реплики по говорящим</span>
            </span>
          </button>
        </div>

        <footer className="flex items-center gap-3 border-t border-ink-700/60 px-5 py-4">
          <p className="font-mono text-[10.5px] leading-tight text-fog-500">
            запуск: <span className="text-fog-300">python scripts/transcribe.py</span>
            <br />в фоновом потоке · логи будут в журнале
          </p>
          <button
            onClick={submit}
            className="sweep relative ml-auto flex items-center gap-2 overflow-hidden rounded-lg bg-acc px-5 py-2.5 text-[13px] font-extrabold text-ink-950 transition-all duration-200 hover:-translate-y-px hover:bg-[#4ae6d6] hover:shadow-[0_10px_28px_-8px_rgba(44,217,200,0.6)] active:translate-y-0"
          >
            <IcUpload className="h-4 w-4" />
            В очередь
          </button>
        </footer>
      </div>
    </div>
  );
}
