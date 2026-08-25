import { Scales } from "@phosphor-icons/react";
import { motion, useReducedMotion } from "motion/react";
import type { EvaluateResponse } from "../lib/types";
import { ClaimList } from "./ClaimList";
import { VerdictPanel } from "./VerdictPanel";

type DocketProps = {
  loading: boolean;
  result: EvaluateResponse | null;
};

export function Docket({ loading, result }: DocketProps) {
  const reduceMotion = useReducedMotion();

  return (
    <section
      id="docket"
      tabIndex={-1}
      aria-live="polite"
      aria-busy={loading}
      className="scroll-mt-20 outline-none"
    >
      <h2 className="sr-only">Evaluation docket</h2>
      {loading ? <DocketSkeleton /> : null}
      {!loading && !result ? <EmptyDocket /> : null}
      {!loading && result ? (
        <motion.div
          className="grid gap-4"
          initial={reduceMotion ? false : { opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.45, ease: [0.16, 1, 0.3, 1] }}
        >
          <VerdictPanel result={result} />
          <ClaimList result={result} />
        </motion.div>
      ) : null}
    </section>
  );
}

function EmptyDocket() {
  return (
    <div className="flex min-h-[22rem] flex-col justify-center rounded-lg border border-dashed border-line bg-raised px-5 py-6 md:min-h-[28rem] md:px-6">
      <Scales
        size={28}
        weight="regular"
        aria-hidden="true"
        className="text-muted"
      />
      <p className="mt-4 max-w-[42ch] text-lg font-medium tracking-tight text-ink">
        The docket is empty
      </p>
      <p className="mt-2 max-w-[52ch] text-base leading-relaxed text-muted">
        Paste a question and the model answer, then evaluate. Claims, judge
        votes, and a preliminary score will land here.
      </p>
    </div>
  );
}

function DocketSkeleton() {
  return (
    <div className="grid gap-4" aria-hidden="true">
      <div className="rounded-lg border border-line bg-raised p-5 md:p-6">
        <div className="h-4 w-28 rounded-md bg-inset" />
        <div className="mt-4 h-16 w-40 rounded-md bg-inset" />
        <div className="mt-6 grid grid-cols-3 gap-4">
          <div className="h-14 rounded-md bg-inset" />
          <div className="h-14 rounded-md bg-inset" />
          <div className="h-14 rounded-md bg-inset" />
        </div>
      </div>
      <div className="rounded-lg border border-line bg-raised p-5 md:p-6">
        <div className="h-4 w-20 rounded-md bg-inset" />
        <div className="mt-4 h-24 rounded-md bg-inset" />
        <div className="mt-3 h-24 rounded-md bg-inset" />
      </div>
    </div>
  );
}
