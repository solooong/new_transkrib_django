export type TaskStatus = "pending" | "running" | "done" | "error";

export type LogLevel = "info" | "ok" | "warn" | "err";

export interface LogLine {
  t: number;
  text: string;
  level: LogLevel;
}

export interface TranscriptSegment {
  start: number;
  end: number;
  speaker: string;
  text: string;
}

export interface Task {
  id: string;
  fileName: string;
  sizeMb: number;
  durationSec: number;
  language: string;
  model: string;
  diarization: boolean;
  status: TaskStatus;
  progress: number;
  createdAt: number;
  finishedAt?: number;
  error?: string;
  log: LogLine[];
  transcript?: TranscriptSegment[];
  words?: number;
  confidence?: number;
  speakers?: number;
}

export interface ToastItem {
  id: number;
  kind: "success" | "error" | "info";
  title: string;
  text?: string;
}

export interface EventItem {
  id: number;
  t: number;
  kind: "start" | "done" | "error" | "queue" | "retry";
  text: string;
}

export interface SystemMetrics {
  cpu: number[];
  ram: number[];
  disk: number;
  gpu: number;
  load: number;
}

export type ViewId = "overview" | "tasks";
