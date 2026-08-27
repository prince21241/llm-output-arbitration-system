import { Scales } from "@phosphor-icons/react";
import { Link, NavLink, useLocation } from "react-router-dom";
import { Show, UserButton } from "@clerk/react";
import { useAuthStatus } from "../lib/authStatus";
import { judgeRoster } from "../lib/format";

type HeaderProps = {
  apiReady?: boolean | null;
  judgeMode?: "live" | "mock";
  judges?: string[];
  tone?: "default" | "cinematic";
};

export function Header({
  apiReady = null,
  judgeMode,
  judges = [],
  tone = "default",
}: HeaderProps) {
  const location = useLocation();
  const { clerkEnabled, isLoaded, isSignedIn } = useAuthStatus();
  const onEvaluate = location.pathname.startsWith("/evaluate");
  const statusLabel =
    apiReady === null ? "Checking API" : apiReady ? "API ready" : "API down";
  const roster =
    judges.length > 0
      ? judgeRoster(judgeMode, judges)
      : apiReady === null
        ? "Checking judges"
        : "Judges unavailable";

  const cinematic = tone === "cinematic";

  return (
    <header
      className={
        cinematic
          ? "sticky top-0 z-[var(--z-header)] border-b border-white/15 bg-[#080104]/35 backdrop-blur-md"
          : "sticky top-0 z-[var(--z-header)] border-b border-line bg-canvas/90 backdrop-blur-md"
      }
    >
      <div className="mx-auto flex h-16 max-w-[1400px] items-center gap-3 px-4">
        <Link
          to="/"
          className={
            cinematic
              ? "inline-flex items-center gap-2 text-[#f2f3f4] no-underline"
              : "inline-flex items-center gap-2 text-ink no-underline"
          }
        >
          <span
            className={
              cinematic
                ? "inline-flex size-11 items-center justify-center rounded-xl border-2 border-white/90 bg-[#080104]/40"
                : undefined
            }
          >
            <Scales size={cinematic ? 20 : 22} weight="regular" aria-hidden="true" />
          </span>
          <span className="text-[17px] font-semibold tracking-tight">
            Arbitrator
          </span>
        </Link>
        {onEvaluate ? (
          <p className="hidden text-sm text-muted sm:block">{roster}</p>
        ) : null}
        {isLoaded && isSignedIn ? (
          <nav className="hidden items-center gap-1 sm:flex" aria-label="Workspace">
            <HeaderNavLink to="/evaluate" cinematic={cinematic}>
              Docket
            </HeaderNavLink>
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
          {clerkEnabled ? (
            <>
              <Show when="signed-out">
                <HeaderSignedOutLinks cinematic={cinematic} />
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
            </>
          ) : (
            <HeaderSignedOutLinks cinematic={cinematic} />
          )}
        </div>
      </div>
    </header>
  );
}

function HeaderSignedOutLinks({ cinematic = false }: { cinematic?: boolean }) {
  return (
    <>
      <Link
        to="/sign-in"
        className={
          cinematic
            ? "welcome-glass inline-flex min-h-11 items-center rounded-full px-4 text-sm font-medium text-[#f2f3f4] no-underline md:min-h-9"
            : "inline-flex min-h-11 items-center rounded-md px-3 text-sm font-medium text-ink no-underline hover:bg-inset md:min-h-9"
        }
      >
        Sign in
      </Link>
      <Link
        to="/sign-up"
        className={
          cinematic
            ? "inline-flex min-h-11 items-center rounded-full bg-accent px-4 text-sm font-semibold text-accent-fg no-underline hover:opacity-90 md:min-h-9"
            : "inline-flex min-h-11 items-center rounded-md bg-accent px-3 text-sm font-semibold text-accent-fg no-underline hover:opacity-90 md:min-h-9"
        }
      >
        Create account
      </Link>
    </>
  );
}

function HeaderNavLink({
  to,
  children,
  cinematic = false,
}: {
  to: string;
  children: string;
  cinematic?: boolean;
}) {
  return (
    <NavLink
      to={to}
      className={({ isActive }) =>
        [
          "inline-flex min-h-9 items-center rounded-md px-3 text-sm no-underline",
          cinematic
            ? isActive
              ? "bg-white/10 font-medium text-[#f2f3f4]"
              : "text-white/70 hover:bg-white/10 hover:text-[#f2f3f4]"
            : isActive
              ? "bg-inset font-medium text-ink"
              : "text-muted hover:bg-inset hover:text-ink",
        ].join(" ")
      }
    >
      {children}
    </NavLink>
  );
}
