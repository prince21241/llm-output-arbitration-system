import type { EvaluateResponse } from "../lib/types";
import { percent, verdictClass, verdictLabel } from "../lib/format";

type VerdictPanelProps = {
  result: EvaluateResponse;
};

export function VerdictPanel({ result }: VerdictPanelProps) {
  return (
    <div className="rounded-lg border border-line bg-raised p-5 md:grid md:grid-cols-12 md:gap-8 md:p-6">
      <div className="md:col-span-7">
        <p className="text-sm font-medium text-muted">Preliminary verdict</p>
        <p
          className={`mt-2 font-mono text-5xl font-semibold tracking-tight tabular-nums leading-[1.1] md:text-6xl ${verdictClass(result.verdict)}`}
        >
          {percent(result.final_confidence)}
        </p>
        <p className={`mt-2 text-lg font-semibold ${verdictClass(result.verdict)}`}>
          {verdictLabel(result.verdict)}
        </p>
        <p className="mt-3 max-w-[65ch] text-sm leading-relaxed text-muted">
          {result.scorer === "ml"
            ? "This is a model estimate from judge votes and evidence overlap. Retrain after you label live votes."
            : "This is a signed-confidence average from the registered judges, not a calibrated probability."}
        </p>
      </div>
      <dl className="mt-6 grid grid-cols-3 gap-3 border-t border-line pt-5 md:col-span-5 md:mt-0 md:border-t-0 md:pt-0">
        <Score
          label="Support"
          value={percent(result.consensus.support_score)}
        />
        <Score
          label="Agreement"
          value={percent(result.consensus.agreement_score)}
        />
        <Score
          label="Dispute"
          value={percent(result.consensus.disagreement_score)}
        />
      </dl>
    </div>
  );
}

function Score({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <dt className="text-sm text-muted">{label}</dt>
      <dd className="mt-1 font-mono text-xl tabular-nums text-ink">{value}</dd>
    </div>
  );
}
