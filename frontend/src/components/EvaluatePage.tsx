import { useEffect, useState } from "react";
import { useAuth } from "@clerk/react";
import { Header } from "./Header";
import { Intake } from "./Intake";
import { Docket } from "./Docket";
import { evaluateAnswer, fetchHealth } from "../lib/api";
import type { EvaluateResponse } from "../lib/types";

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

export function EvaluatePage() {
  const { getToken } = useAuth();
  const [question, setQuestion] = useState(() => readDraft().question);
  const [answer, setAnswer] = useState(() => readDraft().answer);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [fieldErrors, setFieldErrors] = useState<{
    question?: string;
    answer?: string;
  }>({});
  const [result, setResult] = useState<EvaluateResponse | null>(null);
  const [apiReady, setApiReady] = useState<boolean | null>(null);
  const [judgeMode, setJudgeMode] = useState<"live" | "mock" | undefined>(
    undefined,
  );
  const [judges, setJudges] = useState<string[]>([]);

  useEffect(() => {
    sessionStorage.setItem(DRAFT_KEY, JSON.stringify({ question, answer }));
  }, [question, answer]);

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
      requestAnimationFrame(() => {
        document.getElementById("docket")?.focus({ preventScroll: false });
        document.getElementById("docket")?.scrollIntoView({
          behavior: window.matchMedia("(prefers-reduced-motion: reduce)")
            .matches
            ? "auto"
            : "smooth",
          block: "start",
        });
      });
    } catch (err) {
      setResult(null);
      setError(
        err instanceof Error ? err.message : "Evaluation did not complete.",
      );
    } finally {
      setLoading(false);
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
        <div className="lg:col-span-5">
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
        </div>
        <div className="lg:col-span-7">
          <Docket loading={loading} result={result} />
        </div>
      </main>
    </div>
  );
}
