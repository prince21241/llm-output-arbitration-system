import { ClockCounterClockwise, Trash } from "@phosphor-icons/react";
import type { SavedDocket } from "../lib/types";
import {
  formatSavedAt,
  percent,
  verdictClass,
  verdictLabel,
} from "../lib/format";

type HistoryListProps = {
  items: SavedDocket[];
  activeId: string | null;
  onOpen: (item: SavedDocket) => void;
  onRemove: (id: string) => void;
};

export function HistoryList({
  items,
  activeId,
  onOpen,
  onRemove,
}: HistoryListProps) {
  return (
    <section
      aria-labelledby="saved-dockets-heading"
      className="rounded-lg border border-line bg-raised"
    >
      <div className="border-b border-line px-5 py-4 md:px-6">
        <h2
          id="saved-dockets-heading"
          className="flex items-center gap-2 text-lg font-semibold tracking-tight text-ink"
        >
          <ClockCounterClockwise size={20} weight="regular" aria-hidden="true" />
          Saved dockets
        </h2>
        <p className="mt-1 max-w-[65ch] text-sm text-muted">
          Saved to your account. Other people cannot see these dockets.
        </p>
      </div>
      {items.length === 0 ? (
        <p className="px-5 py-5 text-sm leading-relaxed text-muted md:px-6">
          After you evaluate, the docket is stored on your account so a
          refresh does not wipe it.
        </p>
      ) : (
        <ul className="divide-y divide-line">
          {items.map((item) => {
            const selected = item.id === activeId;
            return (
              <li key={item.id} className="flex items-stretch">
                <button
                  type="button"
                  onClick={() => onOpen(item)}
                  aria-current={selected ? "true" : undefined}
                  className={[
                    "flex min-h-11 min-w-0 flex-1 flex-col items-start gap-1 px-5 py-3 text-left md:px-6",
                    selected ? "bg-inset" : "hover:bg-inset/70",
                  ].join(" ")}
                >
                  <span className="w-full truncate text-sm font-medium text-ink">
                    {item.result.question}
                  </span>
                  <span className="flex flex-wrap items-center gap-x-2 gap-y-1 text-sm">
                    <span
                      className={`font-medium ${verdictClass(item.result.verdict)}`}
                    >
                      {verdictLabel(item.result.verdict)}
                    </span>
                    <span className="font-mono tabular-nums text-muted">
                      {percent(item.result.final_confidence)}
                    </span>
                    <span className="text-muted">
                      {formatSavedAt(item.saved_at)}
                    </span>
                  </span>
                </button>
                <button
                  type="button"
                  onClick={() => onRemove(item.id)}
                  aria-label={`Remove saved docket: ${item.result.question}`}
                  className="inline-flex min-h-11 min-w-11 items-center justify-center text-muted hover:text-incorrect"
                >
                  <Trash size={16} weight="regular" aria-hidden="true" />
                </button>
              </li>
            );
          })}
        </ul>
      )}
    </section>
  );
}
