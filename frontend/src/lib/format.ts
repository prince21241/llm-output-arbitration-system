import type { Verdict } from "./types";

export function percent(value: number): string {
  return `${(value * 100).toFixed(1)}%`;
}

const JUDGE_LABELS: Record<string, string> = {
  openai: "OpenAI",
  claude: "Claude",
  gemini: "Gemini",
  mock_judge_a: "Mock A",
  mock_judge_b: "Mock B",
};

export function judgeLabel(id: string): string {
  if (JUDGE_LABELS[id]) return JUDGE_LABELS[id];
  return id.replaceAll("_", " ").replace(/\b[a-z]/g, (char) => char.toUpperCase());
}

export function judgeRoster(mode: "live" | "mock" | undefined, judges: string[]): string {
  if (mode === "mock" || judges.every((id) => id.startsWith("mock_"))) {
    return "Mock judges";
  }
  if (!judges.length) return "Live judges";
  return judges.map(judgeLabel).join(", ");
}

export function verdictLabel(verdict: Verdict): string {
  if (verdict === "supported") return "Supported";
  if (verdict === "incorrect") return "Incorrect";
  return "Uncertain";
}

export function verdictClass(verdict: Verdict): string {
  if (verdict === "supported") return "text-supported";
  if (verdict === "incorrect") return "text-incorrect";
  return "text-uncertain";
}

export function formatSavedAt(iso: string): string {
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return "Unknown time";
  const delta = Date.now() - date.getTime();
  if (delta >= 0 && delta < 60_000) return "Just now";
  return date.toLocaleString(undefined, {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}

export const EXAMPLES = [
  {
    id: "incorrect-date",
    label: "Incorrect date",
    question: "When was the first iPhone released?",
    answer: "The first iPhone was released in 2005.",
  },
  {
    id: "supported-date",
    label: "Supported date",
    question: "When was the first iPhone released?",
    answer: "The first iPhone was released in 2007.",
  },
] as const;
