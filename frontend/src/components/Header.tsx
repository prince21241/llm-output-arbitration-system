import { Scales } from "@phosphor-icons/react";
import { ThemeToggle } from "./ThemeToggle";

type HeaderProps = {
  apiReady: boolean | null;
};

export function Header({ apiReady }: HeaderProps) {
  const statusLabel =
    apiReady === null ? "Checking API" : apiReady ? "API ready" : "API down";

  return (
    <header className="sticky top-0 z-[var(--z-header)] border-b border-line bg-canvas/90 backdrop-blur-md">
      <div className="mx-auto flex h-16 max-w-[1400px] items-center gap-3 px-4">
        <a
          href="#intake"
          className="inline-flex items-center gap-2 text-ink no-underline"
        >
          <Scales size={22} weight="regular" aria-hidden="true" />
          <span className="text-[17px] font-semibold tracking-tight">
            Arbitrator
          </span>
        </a>
        <p className="hidden text-sm text-muted sm:block">
          Phase 1 mock judges
        </p>
        <div className="ml-auto flex items-center gap-2">
          <p
            className="flex items-center gap-2 text-sm text-muted"
            aria-live="polite"
          >
            <span
              className={[
                "size-2 rounded-full",
                apiReady === null
                  ? "bg-muted"
                  : apiReady
                    ? "bg-supported"
                    : "bg-incorrect",
              ].join(" ")}
              aria-hidden="true"
            />
            <span>{statusLabel}</span>
          </p>
          <ThemeToggle />
        </div>
      </div>
    </header>
  );
}
