import { Scales } from "@phosphor-icons/react";
import { Link } from "react-router-dom";
import { useAuthStatus } from "../lib/authStatus";

const linkClass =
  "inline-flex min-h-11 items-center text-sm text-white/70 no-underline transition-colors duration-150 hover:text-[#f2f3f4] md:min-h-9";

export function WelcomeFooter() {
  const { isLoaded, isSignedIn } = useAuthStatus();
  const signedIn = Boolean(isLoaded && isSignedIn);

  return (
    <footer className="border-t border-white/10 bg-[#080104] pb-[env(safe-area-inset-bottom)]">
      <div className="mx-auto grid max-w-[1400px] grid-cols-1 gap-10 px-4 py-16 sm:grid-cols-2 lg:grid-cols-12 lg:gap-8 lg:py-20">
        <div className="sm:col-span-2 lg:col-span-6">
          <p className="inline-flex items-center gap-2 text-[#f2f3f4]">
            <span className="inline-flex size-11 items-center justify-center rounded-xl border-2 border-white/90 bg-[#080104]/40">
              <Scales size={20} weight="regular" aria-hidden="true" />
            </span>
            <span className="text-[17px] font-semibold tracking-tight" translate="no">
              Arbitrator
            </span>
          </p>
          <p className="mt-4 max-w-[36ch] text-sm leading-relaxed text-white/70">
            Independent judges vote on each extracted claim. You get a
            preliminary score, not a guarantee.
          </p>
        </div>

        <nav aria-label="On this page" className="lg:col-span-3">
          <p className="text-sm font-medium text-[#f2f3f4]">On this page</p>
          <ul className="mt-3 grid gap-1">
            <li>
              <a className={linkClass} href="#how-it-works">
                How it works
              </a>
            </li>
            <li>
              <a className={linkClass} href="#sample-score">
                Sample score
              </a>
            </li>
            <li>
              <a className={linkClass} href="#open-docket">
                {signedIn ? "Open a docket" : "Start a docket"}
              </a>
            </li>
          </ul>
        </nav>

        <nav aria-label="Account" className="lg:col-span-3">
          <p className="text-sm font-medium text-[#f2f3f4]">Account</p>
          <ul className="mt-3 grid gap-1">
            {signedIn ? (
              <li>
                <Link className={linkClass} to="/evaluate">
                  Docket
                </Link>
              </li>
            ) : (
              <>
                <li>
                  <Link className={linkClass} to="/sign-in">
                    Sign in
                  </Link>
                </li>
                <li>
                  <Link className={linkClass} to="/sign-up">
                    Create account
                  </Link>
                </li>
              </>
            )}
          </ul>
        </nav>
      </div>

      <div className="border-t border-white/10">
        <div className="mx-auto flex max-w-[1400px] flex-col gap-2 px-4 py-6 sm:flex-row sm:items-center sm:justify-between">
          <p className="text-sm text-white/70">
            <span translate="no">Arbitrator</span>
          </p>
          <p className="text-sm text-white/70">
            Preliminary scores. Not a guarantee.
          </p>
        </div>
      </div>
    </footer>
  );
}
