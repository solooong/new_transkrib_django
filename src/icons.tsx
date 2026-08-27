import type { SVGProps } from "react";

type P = SVGProps<SVGSVGElement>;

function base(props: P) {
  return {
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: "currentColor",
    strokeWidth: 1.7,
    strokeLinecap: "round" as const,
    strokeLinejoin: "round" as const,
    "aria-hidden": true,
    ...props,
  };
}

/* Фирменный знак: столбики волны в скруглённом квадрате */
export function LogoMark(props: P) {
  return (
    <svg viewBox="0 0 48 48" fill="none" aria-hidden {...props}>
      <rect x="1.5" y="1.5" width="45" height="45" rx="13" fill="#0F1A2E" stroke="rgba(44,217,200,0.45)" strokeWidth="1.5" />
      <g stroke="#2CD9C8" strokeWidth="3.4" strokeLinecap="round">
        <path d="M12 20v8" />
        <path d="M18 15v18" />
        <path d="M24 10v28" stroke="#F2A33C" />
        <path d="M30 16v16" />
        <path d="M36 21v6" />
      </g>
    </svg>
  );
}

export const IcGrid = (p: P) => (
  <svg {...base(p)}>
    <rect x="3.5" y="3.5" width="7" height="7" rx="1.8" />
    <rect x="13.5" y="3.5" width="7" height="7" rx="1.8" />
    <rect x="3.5" y="13.5" width="7" height="7" rx="1.8" />
    <path d="M17 13.5v7M13.5 17h7" />
  </svg>
);

export const IcTasks = (p: P) => (
  <svg {...base(p)}>
    <path d="M4 6.5h9M4 12h13M4 17.5h7" />
    <path d="M17.5 5.5l1.4 1.4 2.6-2.9" />
    <path d="M16 16.5l2 2 3.5-4" />
  </svg>
);

export const IcUpload = (p: P) => (
  <svg {...base(p)}>
    <path d="M12 15V4.5" />
    <path d="M7.5 8.5L12 4l4.5 4.5" />
    <path d="M4.5 15.5v2.5a2 2 0 0 0 2 2h11a2 2 0 0 0 2-2v-2.5" />
  </svg>
);

export const IcSearch = (p: P) => (
  <svg {...base(p)}>
    <circle cx="10.8" cy="10.8" r="6.3" />
    <path d="M15.5 15.5L20 20" />
  </svg>
);

export const IcClose = (p: P) => (
  <svg {...base(p)}>
    <path d="M6 6l12 12M18 6L6 18" />
  </svg>
);

export const IcPlay = (p: P) => (
  <svg {...base(p)} fill="currentColor" strokeWidth="0">
    <path d="M8.2 5.4c0-.9 1-1.5 1.8-1L19 11a1.2 1.2 0 0 1 0 2l-9 6.6c-.8.5-1.8-.1-1.8-1V5.4z" />
  </svg>
);

export const IcPause = (p: P) => (
  <svg {...base(p)} fill="currentColor" strokeWidth="0">
    <rect x="6.5" y="4.5" width="3.6" height="15" rx="1.2" />
    <rect x="13.9" y="4.5" width="3.6" height="15" rx="1.2" />
  </svg>
);

export const IcDownload = (p: P) => (
  <svg {...base(p)}>
    <path d="M12 4.5V15" />
    <path d="M7.5 11L12 15.5 16.5 11" />
    <path d="M4.5 16v2a2 2 0 0 0 2 2h11a2 2 0 0 0 2-2v-2" />
  </svg>
);

export const IcRetry = (p: P) => (
  <svg {...base(p)}>
    <path d="M5 8.5A8 8 0 1 1 4 13" />
    <path d="M5 3.5v5h5" />
  </svg>
);

export const IcTrash = (p: P) => (
  <svg {...base(p)}>
    <path d="M4.5 6.5h15" />
    <path d="M9.5 6V4.8a1.3 1.3 0 0 1 1.3-1.3h2.4a1.3 1.3 0 0 1 1.3 1.3V6" />
    <path d="M6.5 6.5l.8 12.2a1.8 1.8 0 0 0 1.8 1.8h5.8a1.8 1.8 0 0 0 1.8-1.8l.8-12.2" />
    <path d="M10 10.5v6M14 10.5v6" />
  </svg>
);

export const IcCpu = (p: P) => (
  <svg {...base(p)}>
    <rect x="6.5" y="6.5" width="11" height="11" rx="2" />
    <rect x="10" y="10" width="4" height="4" rx="1" />
    <path d="M9 3.5v3M15 3.5v3M9 17.5v3M15 17.5v3M3.5 9h3M3.5 15h3M17.5 9h3M17.5 15h3" />
  </svg>
);

export const IcRam = (p: P) => (
  <svg {...base(p)}>
    <rect x="3.5" y="7" width="17" height="9" rx="1.6" />
    <path d="M7 10.5v2M10.3 10.5v2M13.7 10.5v2M17 10.5v2M6.5 16v2.5M17.5 16v2.5" />
  </svg>
);

export const IcDisk = (p: P) => (
  <svg {...base(p)}>
    <circle cx="12" cy="12" r="8.5" />
    <circle cx="12" cy="12" r="2.4" />
    <path d="M12 3.5v3" />
  </svg>
);

export const IcGpu = (p: P) => (
  <svg {...base(p)}>
    <rect x="3.5" y="6.5" width="17" height="11" rx="2" />
    <circle cx="9" cy="12" r="2.6" />
    <path d="M15.5 9.5h2.5M15.5 12h2.5M15.5 14.5h2.5M7 17.5v2M13 17.5v2" />
  </svg>
);

export const IcDoc = (p: P) => (
  <svg {...base(p)}>
    <path d="M6 4.5h8l4 4V19a1.5 1.5 0 0 1-1.5 1.5h-9A1.5 1.5 0 0 1 6 19V4.5z" />
    <path d="M14 4.5V9h4" />
    <path d="M9 13h6M9 16.2h4" />
  </svg>
);

export const IcCheck = (p: P) => (
  <svg {...base(p)}>
    <path d="M4.5 12.5l5 5L19.5 6.5" />
  </svg>
);

export const IcAlert = (p: P) => (
  <svg {...base(p)}>
    <path d="M12 4L2.8 19.5h18.4L12 4z" />
    <path d="M12 10v4.2M12 17.2v.3" />
  </svg>
);

export const IcClock = (p: P) => (
  <svg {...base(p)}>
    <circle cx="12" cy="12" r="8.5" />
    <path d="M12 7.5V12l3.2 2" />
  </svg>
);

export const IcChevronR = (p: P) => (
  <svg {...base(p)}>
    <path d="M9.5 6l6 6-6 6" />
  </svg>
);

export const IcTerminal = (p: P) => (
  <svg {...base(p)}>
    <rect x="3.5" y="4.5" width="17" height="15" rx="2" />
    <path d="M7 9.5l3 2.8-3 2.8M12.5 15.5H17" />
  </svg>
);

export const IcBell = (p: P) => (
  <svg {...base(p)}>
    <path d="M6 16v-5.5a6 6 0 1 1 12 0V16l1.5 2.5h-15L6 16z" />
    <path d="M10 21a2.2 2.2 0 0 0 4 0" />
  </svg>
);

export const IcBolt = (p: P) => (
  <svg {...base(p)}>
    <path d="M13 3L5.5 13.5H11L10 21l7.5-10.5H12L13 3z" />
  </svg>
);

export const IcWave = (p: P) => (
  <svg {...base(p)}>
    <path d="M3 12h2M7 8.5v7M11 5.5v13M15 8v8M19 10.5v3" />
  </svg>
);

export const IcArrowUpRight = (p: P) => (
  <svg {...base(p)}>
    <path d="M7 17L17 7M9.5 7H17v7.5" />
  </svg>
);

export const IcSpark = (p: P) => (
  <svg {...base(p)}>
    <path d="M12 3.5l1.9 5.4 5.6 1.6-5.6 1.7L12 17.7l-1.9-5.5-5.6-1.7 5.6-1.6L12 3.5z" />
    <path d="M19 16.5l.8 2.2 2.2.8-2.2.8-.8 2.2-.8-2.2-2.2-.8 2.2-.8.8-2.2z" />
  </svg>
);

export const IcGlobe = (p: P) => (
  <svg {...base(p)}>
    <circle cx="12" cy="12" r="8.5" />
    <path d="M3.5 12h17M12 3.5c2.6 2.3 4 5.2 4 8.5s-1.4 6.2-4 8.5c-2.6-2.3-4-5.2-4-8.5s1.4-6.2 4-8.5z" />
  </svg>
);

export const IcLayers = (p: P) => (
  <svg {...base(p)}>
    <path d="M12 3.5L3.5 8 12 12.5 20.5 8 12 3.5z" />
    <path d="M3.5 12.5L12 17l8.5-4.5" />
    <path d="M3.5 16.5L12 21l8.5-4.5" />
  </svg>
);

export const IcAudioFile = (p: P) => (
  <svg {...base(p)}>
    <path d="M6 4.5h8l4 4V19a1.5 1.5 0 0 1-1.5 1.5h-9A1.5 1.5 0 0 1 6 19V4.5z" />
    <path d="M14 4.5V9h4" />
    <path d="M9.5 15.5v-2M12 16.5v-4M14.5 15.8v-2.6" />
  </svg>
);

export const IcDots = (p: P) => (
  <svg {...base(p)} fill="currentColor" strokeWidth="0">
    <circle cx="5.5" cy="12" r="1.5" />
    <circle cx="12" cy="12" r="1.5" />
    <circle cx="18.5" cy="12" r="1.5" />
  </svg>
);
