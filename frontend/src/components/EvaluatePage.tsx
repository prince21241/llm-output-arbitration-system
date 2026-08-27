import { useEffect, useState } from "react";
import { useAuth } from "@clerk/react";
import { Header } from "./Header";
import { HistoryList } from "./HistoryList";
import { Intake } from "./Intake";
import { Docket } from "./Docket";
import {
  deleteDocket,
  evaluateAnswer,
  fetchHealth,
  listDockets,
} from "../lib/api";
import { readActiveId, writeActiveId } from "../lib/history";
import type { EvaluateResponse, SavedDocket } from "../lib/types";

const DRAFT_KEY = "arbitrator-draft";
const MIN_LOADING_MS = 400;

type Draft = { question: string; answer: string };

function readDraft(): Draft {
  try {
    const raw = sessionStorage.getItem(DRAFT_KEY);
    if (!raw) return { question: "", answer: "" };
    const parsed = JSON.parse(raw) as Draft;
    return {
      question: typeof parsed.question === "string" ? parsed.question : "",
      answer: typeof parsed.answer === "string" ? parsed.answer : "",
    };
  } catch {
    return { question: "", answer: "" };
  }
}

function focusDocket() {
  requestAnimationFrame(() => {
    document.getElementById("docket")?.focus({ preventScroll: false });
    document.getElementById("docket")?.scrollIntoView({
      behavior: window.matchMedia("(prefers-reduced-motion: reduce)").matches
        ? "auto"
        : "smooth",
      block: "start",
    });
  });
}

export function EvaluatePage() {
  const { getToken, userId } = useAuth();
  const [question, setQuestion] = useState(() => readDraft().question);
  const [answer, setAnswer] = useState(() => readDraft().answer);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [fieldErrors, setFieldErrors] = useState<{
    question?: string;
    answer?: string;
  }>({});
  const [result, setResult] = useState<EvaluateResponse | null>(null);
  const [history, setHistory] = useState<SavedDocket[]>([]);
  const [activeId, setActiveId] = useState<string | null>(null);
  const [apiReady, setApiReady] = useState<boolean | null>(null);
  const [judgeMode, setJudgeMode] = useState<"live" | "mock" | undefined>(
    undefined,
  );
  const [judges, setJudges] = useState<string[]>([]);

  useEffect(() => {
    sessionStorage.setItem(DRAFT_KEY, JSON.stringify({ question, answer }));
  }, [question, answer]);

  useEffect(() => {
    if (!userId) return;
    let cancelled = false;
    (async () => {
      try {
        const token = await getToken();
        const items = await listDockets(token);
        if (cancelled) return;
        setHistory(items);
        const storedId = readActiveId(userId);
        const match = items.find((item) => item.id === storedId) ?? items[0];
        if (!match) return;
        setActiveId(match.id);
        setResult(match.result);
        writeActiveId(userId, match.id);
      } catch {
        if (!cancelled) setHistory([]);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [userId, getToken]);

  useEffect(() => {
    let cancelled = false;
    fetchHealth().then((health) => {
      if (!cancelled) {
        setApiReady(health?.status === "ok");
        setJudgeMode(health?.mode);
        setJudges(health?.judges ?? []);
      }
    });
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (error) {
      const node = document.getElementById("intake-error");
      node?.focus();
    }
  }, [error]);

  function validate(): boolean {
    const next: { question?: string; answer?: string } = {};
    if (!question.trim()) next.question = "Enter a question.";
    if (!answer.trim()) next.answer = "Enter the model answer.";
    setFieldErrors(next);
    return Object.keys(next).length === 0;
  }

  async function onSubmit() {
    setError(null);
    if (!validate()) {
      const first = !question.trim() ? "question" : "answer";
      document
        .querySelector<HTMLTextAreaElement>(`textarea[name="${first}"]`)
        ?.focus();
      return;
    }

    setLoading(true);
    const started = performance.now();
    try {
      const token = await getToken();
      const data = await evaluateAnswer(question.trim(), answer.trim(), token);
      const wait = Math.max(0, MIN_LOADING_MS - (performance.now() - started));
      if (wait) {
        await new Promise((resolve) => setTimeout(resolve, wait));
      }
      setResult(data);
      if (data.id && userId) {
        setActiveId(data.id);
        writeActiveId(userId, data.id);
      }
      try {
        setHistory(await listDockets(token));
      } catch {
        /* the new verdict is already on screen */
      }
      focusDocket();
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Evaluation did not complete.",
      );
    } finally {
      setLoading(false);
    }
  }

  function onOpenSaved(item: SavedDocket) {
    if (!userId) return;
    setQuestion(item.result.question);
    setAnswer(item.result.answer);
    setResult(item.result);
    setActiveId(item.id);
    writeActiveId(userId, item.id);
    setError(null);
    setFieldErrors({});
    focusDocket();
  }

  async function onRemoveSaved(id: string) {
    if (!userId) return;
    try {
      const token = await getToken();
      await deleteDocket(id, token);
      const next = history.filter((item) => item.id !== id);
      setHistory(next);
      if (activeId === id) {
        setActiveId(null);
        setResult(null);
        writeActiveId(userId, null);
      }
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Could not remove that docket.",
      );
    }
  }

  return (
    <div className="min-h-[100dvh] bg-canvas text-ink">
      <a
        href="#intake"
        className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-3 focus:z-[var(--z-overlay)] focus:rounded-md focus:bg-raised focus:px-3 focus:py-2"
      >
        Skip to form
      </a>
      <Header apiReady={apiReady} judgeMode={judgeMode} judges={judges} />
      <main className="mx-auto grid max-w-[1400px] grid-cols-1 gap-6 px-4 py-6 lg:grid-cols-12 lg:items-start">
        <div className="grid gap-4 lg:col-span-5">
          <Intake
            question={question}
            answer={answer}
            error={error}
            fieldErrors={fieldErrors}
            loading={loading}
            onQuestionChange={(value) => {
              setQuestion(value);
              if (fieldErrors.question) {
                setFieldErrors((current) => ({ ...current, question: undefined }));
              }
            }}
            onAnswerChange={(value) => {
              setAnswer(value);
              if (fieldErrors.answer) {
                setFieldErrors((current) => ({ ...current, answer: undefined }));
              }
            }}
            onSubmit={onSubmit}
            onLoadExample={(nextQuestion, nextAnswer) => {
              setQuestion(nextQuestion);
              setAnswer(nextAnswer);
              setFieldErrors({});
              setError(null);
            }}
          />
          <HistoryList
            items={history}
            activeId={activeId}
            onOpen={onOpenSaved}
            onRemove={onRemoveSaved}
          />
        </div>
        <div className="lg:col-span-7">
          <Docket
            loading={loading}
            result={result}
            hasHistory={history.length > 0}
          />
        </div>
      </main>
    </div>
  );
}
