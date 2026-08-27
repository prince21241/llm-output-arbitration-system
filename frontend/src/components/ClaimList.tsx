import { BookOpen, CaretDown } from "@phosphor-icons/react";
import type { Claim, EvaluateResponse, JudgeResult } from "../lib/types";
import {
  judgeLabel,
  percent,
  verdictClass,
  verdictLabel,
} from "../lib/format";

type ClaimListProps = {
  result: EvaluateResponse;
};

export function ClaimList({ result }: ClaimListProps) {
  return (
    <div className="rounded-lg border border-line bg-raised">
      <div className="border-b border-line px-5 py-4 md:px-6">
        <h3 className="text-lg font-semibold tracking-tight text-ink">
          Claims
        </h3>
        <p className="mt-1 text-sm text-muted">
          {result.claims.length} extracted
          {result.claims.length === 1 ? " claim" : " claims"} from the answer.
        </p>
      </div>
      <ol className="divide-y divide-line">
        {result.claims.map((claim) => {
          const consensus = result.claim_consensus.find(
            (item) => item.claim_id === claim.id,
          );
          const votes = result.judge_results.filter(
            (item) => item.claim_id === claim.id,
          );
          return (
            <li key={claim.id} className="px-5 py-5 md:px-6">
              <ClaimExhibit
                claim={claim}
                votes={votes}
                consensus={consensus}
              />
            </li>
          );
        })}
      </ol>
    </div>
  );
}

function ClaimExhibit({
  claim,
  votes,
  consensus,
}: {
  claim: Claim;
  votes: JudgeResult[];
  consensus: EvaluateResponse["claim_consensus"][number] | undefined;
}) {
  return (
    <article>
      <div className="flex flex-wrap items-baseline gap-x-3 gap-y-1">
        <p className="font-mono text-xs tabular-nums text-muted">{claim.id}</p>
        <p className="text-xs font-medium uppercase tracking-wide text-muted">
          {claim.type}
        </p>
        {consensus ? (
          <p
            className={`text-sm font-semibold ${verdictClass(consensus.verdict)}`}
          >
            {verdictLabel(consensus.verdict)}
          </p>
        ) : null}
      </div>
      <p className="mt-2 max-w-[65ch] text-base leading-relaxed text-ink">
        {claim.text}
      </p>
      {(claim.evidence ?? []).length > 0 ? (
        <ul className="mt-4 grid gap-2">
          {(claim.evidence ?? []).map((item) => (
            <li key={item.url} className="rounded-md border border-line px-3 py-2">
              <a
                href={item.url}
                target="_blank"
                rel="noreferrer noopener"
                className="inline-flex min-h-6 items-center gap-2 text-sm font-medium text-ink"
              >
                <BookOpen size={16} weight="regular" aria-hidden="true" />
                {item.title}
              </a>
              <p className="mt-1 max-w-[65ch] text-sm leading-relaxed text-muted">
                {item.snippet}
              </p>
              <p className="mt-1 font-mono text-xs tabular-nums text-muted">
                {item.source} overlap {percent(item.overlap)}
              </p>
            </li>
          ))}
        </ul>
      ) : (
        <p className="mt-4 max-w-[65ch] text-sm text-muted">
          No Wikipedia snippets matched this claim.
        </p>
      )}
      {consensus ? (
        <p className="mt-3 font-mono text-xs tabular-nums text-muted">
          support {percent(consensus.support_probability)}
          {"  "}
          agreement {percent(consensus.agreement_score)}
          {"  "}
          votes {consensus.supporting_votes} yes / {consensus.incorrect_votes} no
          / {consensus.uncertain_votes} open
        </p>
      ) : null}
      <ul className="mt-4 grid gap-2">
        {votes.map((vote) => (
          <li
            key={`${vote.judge}-${vote.claim_id}`}
            className="rounded-md bg-inset px-3 py-2"
          >
            <details className="group">
              <summary className="flex cursor-pointer list-none items-center gap-2 text-sm text-ink [&::-webkit-details-marker]:hidden">
                <CaretDown
                  size={14}
                  weight="regular"
                  aria-hidden="true"
                  className="shrink-0 text-muted transition-transform duration-200 group-open:rotate-180"
                />
                <span className="font-medium">{judgeLabel(vote.judge)}</span>
                <span
                  className={`ml-auto font-semibold ${verdictClass(vote.verdict)}`}
                >
                  {verdictLabel(vote.verdict)}
                </span>
                <span className="font-mono text-xs tabular-nums text-muted">
                  {percent(vote.confidence)}
                </span>
              </summary>
              <p className="mt-2 max-w-[65ch] pl-6 text-sm leading-relaxed text-muted">
                {vote.reason}
              </p>
            </details>
          </li>
        ))}
      </ul>
    </article>
  );
}
