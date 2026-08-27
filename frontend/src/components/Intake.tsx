import { CircleNotch } from "@phosphor-icons/react";
import { useReducedMotion } from "motion/react";
import { useId, type FormEvent, type KeyboardEvent } from "react";
import { EXAMPLES } from "../lib/format";

type IntakeProps = {
  question: string;
  answer: string;
  error: string | null;
  fieldErrors: { question?: string; answer?: string };
  loading: boolean;
  onQuestionChange: (value: string) => void;
  onAnswerChange: (value: string) => void;
  onSubmit: () => void;
  onLoadExample: (question: string, answer: string) => void;
};

export function Intake({
  question,
  answer,
  error,
  fieldErrors,
  loading,
  onQuestionChange,
  onAnswerChange,
  onSubmit,
  onLoadExample,
}: IntakeProps) {
  const reduceMotion = useReducedMotion();
  const questionId = useId();
  const answerId = useId();
  const questionHelpId = useId();
  const answerHelpId = useId();
  const questionErrorId = useId();
  const answerErrorId = useId();

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    onSubmit();
  }

  function handleKeyDown(event: KeyboardEvent<HTMLFormElement>) {
    if ((event.metaKey || event.ctrlKey) && event.key === "Enter") {
      event.preventDefault();
      onSubmit();
    }
  }

  return (
    <section
      id="intake"
      className="scroll-mt-20 rounded-lg border border-line bg-raised p-5 shadow-[0_1px_0_var(--shadow)] md:p-6"
    >
      <h1 className="max-w-[22ch] text-3xl font-semibold tracking-tight text-ink md:text-4xl">
        Cross-examine the model&apos;s answer
      </h1>
      <p className="mt-3 max-w-[65ch] text-base leading-relaxed text-muted">
        Extract claims, collect independent verdicts, and score agreement.
      </p>

      <form
        className="mt-6 grid gap-5"
        onSubmit={handleSubmit}
        onKeyDown={handleKeyDown}
        noValidate
      >
        <div className="grid gap-2">
          <label htmlFor={questionId} className="text-sm font-medium text-ink">
            Question
          </label>
          <textarea
            id={questionId}
            name="question"
            value={question}
            onChange={(event) => onQuestionChange(event.target.value)}
            rows={3}
            autoComplete="off"
            spellCheck
            placeholder="When was the first iPhone released?…"
            aria-describedby={`${questionHelpId}${fieldErrors.question ? ` ${questionErrorId}` : ""}`}
            aria-invalid={Boolean(fieldErrors.question)}
            className="min-h-[5.5rem] w-full resize-y rounded-md border border-line bg-inset px-3 py-2.5 text-base text-ink placeholder:text-muted/80"
          />
          <p id={questionHelpId} className="text-sm text-muted">
            The original prompt given to the model.
          </p>
          {fieldErrors.question ? (
            <p id={questionErrorId} className="text-sm text-incorrect">
              {fieldErrors.question}
            </p>
          ) : null}
        </div>

        <div className="grid gap-2">
          <label htmlFor={answerId} className="text-sm font-medium text-ink">
            Model answer
          </label>
          <textarea
            id={answerId}
            name="answer"
            value={answer}
            onChange={(event) => onAnswerChange(event.target.value)}
            rows={7}
            autoComplete="off"
            spellCheck
            placeholder="The first iPhone was released in 2005.…"
            aria-describedby={`${answerHelpId}${fieldErrors.answer ? ` ${answerErrorId}` : ""}`}
            aria-invalid={Boolean(fieldErrors.answer)}
            className="min-h-[10rem] w-full resize-y rounded-md border border-line bg-inset px-3 py-2.5 text-base text-ink placeholder:text-muted/80"
          />
          <p id={answerHelpId} className="text-sm text-muted">
            Paste the generated answer. Each statement becomes a claim.
          </p>
          {fieldErrors.answer ? (
            <p id={answerErrorId} className="text-sm text-incorrect">
              {fieldErrors.answer}
            </p>
          ) : null}
        </div>

        {error ? (
          <p
            id="intake-error"
            role="alert"
            tabIndex={-1}
            className="rounded-md border border-incorrect/30 bg-incorrect/10 px-3 py-2 text-sm text-incorrect"
          >
            {error}
          </p>
        ) : null}

        <div className="flex flex-wrap items-center gap-3">
          <button
            type="submit"
            disabled={loading}
            aria-busy={loading}
            className="inline-flex min-h-11 items-center justify-center gap-2 rounded-md bg-accent px-4 text-sm font-semibold text-accent-fg transition-transform duration-150 hover:opacity-90 active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-70"
          >
            {loading ? (
              <>
                <CircleNotch
                  size={16}
                  weight="regular"
                  aria-hidden="true"
                  className={reduceMotion ? undefined : "animate-spin"}
                />
                Evaluating…
              </>
            ) : (
              "Evaluate"
            )}
          </button>
          <p className="text-sm text-muted">Ctrl or Cmd + Enter</p>
        </div>

        <div className="grid gap-2">
          <p className="text-sm font-medium text-ink">Examples</p>
          <div className="flex flex-wrap gap-2">
            {EXAMPLES.map((example) => (
              <button
                key={example.id}
                type="button"
                onClick={() => onLoadExample(example.question, example.answer)}
                className="inline-flex min-h-11 items-center rounded-md border border-line bg-canvas px-3 text-sm text-ink transition-transform duration-150 hover:bg-inset active:scale-[0.98]"
              >
                {example.label}
              </button>
            ))}
          </div>
        </div>
      </form>
    </section>
  );
}
