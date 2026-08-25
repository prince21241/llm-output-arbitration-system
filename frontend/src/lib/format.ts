import type { Verdict } from "./types";

export function percent(value: number): string {
  return `${(value * 100).toFixed(1)}%`;
}

export function judgeLabel(id: string): string {
  return id.replaceAll("_", " ").replace(/\b[a-z]/g, (char) => char.toUpperCase());
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
