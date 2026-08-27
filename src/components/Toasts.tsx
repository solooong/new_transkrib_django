import { useEffect } from "react";
import type { ToastItem } from "../types";
import { IcAlert, IcCheck, IcClose, IcBolt } from "../icons";

function Toast({ toast, onClose }: { toast: ToastItem; onClose: (id: number) => void }) {
  useEffect(() => {
    const t = setTimeout(() => onClose(toast.id), 5200);
    return () => clearTimeout(t);
  }, [toast.id, onClose]);

  const meta = {
    success: { icon: IcCheck, ring: "border-mint/40", tint: "text-mint", bg: "bg-mint/12" },
    error: { icon: IcAlert, ring: "border-coral/40", tint: "text-coral", bg: "bg-coral/12" },
    info: { icon: IcBolt, ring: "border-acc/40", tint: "text-acc", bg: "bg-acc/12" },
  }[toast.kind];

  const Icon = meta.icon;

  return (
    <div
      role="status"
      className={`anim-toast panel pointer-events-auto flex w-[340px] items-start gap-3 overflow-hidden p-3.5 ${meta.ring}`}
    >
      <span className={`mt-0.5 grid h-8 w-8 shrink-0 place-items-center rounded-lg border ${meta.ring} ${meta.bg} ${meta.tint}`}>
        <Icon className="h-4 w-4" />
      </span>
      <div className="min-w-0 flex-1">
        <p className="text-[13px] font-bold leading-tight text-snow">{toast.title}</p>
        {toast.text && <p className="mt-0.5 truncate text-xs text-fog-400">{toast.text}</p>}
      </div>
      <button
        onClick={() => onClose(toast.id)}
        className="rounded-md p-1 text-fog-500 transition hover:bg-ink-700 hover:text-snow"
        aria-label="Закрыть уведомление"
      >
        <IcClose className="h-3.5 w-3.5" />
      </button>
    </div>
  );
}

export default function Toasts({
  items,
  onClose,
}: {
  items: ToastItem[];
  onClose: (id: number) => void;
}) {
  return (
    <div className="pointer-events-none fixed right-4 top-4 z-[70] flex flex-col gap-2.5">
      {items.map((t) => (
        <Toast key={t.id} toast={t} onClose={onClose} />
      ))}
    </div>
  );
}
