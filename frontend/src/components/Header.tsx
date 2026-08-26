import { Scales } from "@phosphor-icons/react";
import { Link, NavLink, useLocation } from "react-router-dom";
import { Show, UserButton, useAuth } from "@clerk/react";
import { ThemeToggle } from "./ThemeToggle";
import { judgeRoster } from "../lib/format";

type HeaderProps = {
  apiReady?: boolean | null;
  judgeMode?: "live" | "mock";
  judges?: string[];
};

export function Header({
  apiReady = null,
  judgeMode,
  judges = [],
}: HeaderProps) {
  const location = useLocation();
  const { isLoaded, isSignedIn } = useAuth();
  const onEvaluate = location.pathname.startsWith("/evaluate");
  const statusLabel =
    apiReady === null ? "Checking API" : apiReady ? "API ready" : "API down";
  const roster =
    judges.length > 0
      ? judgeRoster(judgeMode, judges)
      : apiReady === null
        ? "Checking judges"
        : "Judges unavailable";

  return (
    <header className="sticky top-0 z-[var(--z-header)] border-b border-line bg-canvas/90 backdrop-blur-md">
      <div className="mx-auto flex h-16 max-w-[1400px] items-center gap-3 px-4">
        <Link
          to={isSignedIn ? "/welcome" : "/sign-in"}
          className="inline-flex items-center gap-2 text-ink no-underline"
        >
          <Scales size={22} weight="regular" aria-hidden="true" />
          <span className="text-[17px] font-semibold tracking-tight">
            Arbitrator
          </span>
        </Link>
        {onEvaluate ? (
          <p className="hidden text-sm text-muted sm:block">{roster}</p>
        ) : null}
        {isLoaded && isSignedIn ? (
          <nav className="hidden items-center gap-1 sm:flex" aria-label="Workspace">
            <HeaderNavLink to="/welcome">Welcome</HeaderNavLink>
            <HeaderNavLink to="/evaluate">Docket</HeaderNavLink>
          </nav>
        ) : null}
        <div className="ml-auto flex items-center gap-2">
          {onEvaluate ? (
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
          ) : null}
          <ThemeToggle />
          <Show when="signed-out">
            <Link
              to="/sign-in"
              className="inline-flex min-h-11 items-center rounded-md px-3 text-sm font-medium text-ink no-underline hover:bg-inset md:min-h-9"
            >
              Sign in
            </Link>
            <Link
              to="/sign-up"
              className="inline-flex min-h-11 items-center rounded-md bg-accent px-3 text-sm font-semibold text-accent-fg no-underline hover:opacity-90 md:min-h-9"
            >
              Create account
            </Link>
          </Show>
          <Show when="signed-in">
            <UserButton
              appearance={{
                elements: {
                  avatarBox: "size-8",
                },
              }}
            />
          </Show>
        </div>
      </div>
    </header>
  );
}

function HeaderNavLink({
  to,
  children,
}: {
  to: string;
  children: string;
}) {
  return (
    <NavLink
      to={to}
      className={({ isActive }) =>
        [
          "inline-flex min-h-9 items-center rounded-md px-3 text-sm no-underline",
          isActive
            ? "bg-inset font-medium text-ink"
            : "text-muted hover:bg-inset hover:text-ink",
        ].join(" ")
      }
    >
      {children}
    </NavLink>
  );
}
