import { ArrowRight } from "@phosphor-icons/react";
import { Link } from "react-router-dom";
import { motion, useReducedMotion } from "motion/react";
import { useAuthStatus } from "../lib/authStatus";
import { SAMPLE_EVALUATION } from "../lib/sampleEvaluation";
import { ClaimList } from "./ClaimList";
import { Header } from "./Header";
import { WelcomeFooter } from "./WelcomeFooter";
import { WelcomeHero } from "./WelcomeHero";

export function WelcomePage() {
  const reduceMotion = useReducedMotion();
  const { isLoaded, isSignedIn } = useAuthStatus();
  const signedIn = Boolean(isLoaded && isSignedIn);

  return (
    <div className="min-h-[100dvh] bg-[#080104] text-[#f2f3f4]">
      <a
        href="#welcome-main"
        className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-3 focus:z-[var(--z-overlay)] focus:rounded-md focus:bg-raised focus:px-3 focus:py-2"
      >
        Skip to content
      </a>
      <Header tone="cinematic" />
      <main id="welcome-main">
        <WelcomeHero />

        <section
          id="sample-score"
          aria-labelledby="welcome-exhibit-heading"
          className="relative z-[2] scroll-mt-20 border-t border-white/10 bg-[#10060a]"
        >
          <div className="mx-auto max-w-[1400px] px-4 py-16 lg:py-24">
            <h2
              id="welcome-exhibit-heading"
              className="max-w-[20ch] scroll-mt-20 text-3xl font-semibold tracking-tight text-pretty md:text-4xl"
            >
              Why that score landed
            </h2>
            <p className="mt-3 max-w-[65ch] text-base leading-relaxed text-white/75">
              Open a judge vote to read the reason. This is the same incorrect-date
              example available on the docket.
            </p>
            <motion.div
              className="mt-10"
              initial={reduceMotion ? false : { opacity: 0, y: 16 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, amount: 0.2 }}
              transition={
                reduceMotion
                  ? { duration: 0 }
                  : { duration: 0.5, ease: [0.16, 1, 0.3, 1] }
              }
            >
              <ClaimList result={SAMPLE_EVALUATION} />
            </motion.div>
          </div>
        </section>

        <section
          id="open-docket"
          aria-labelledby="welcome-close-heading"
          className="scroll-mt-20 border-t border-white/10"
        >
          <div className="mx-auto max-w-[1400px] px-4 py-16 lg:py-24">
            <h2
              id="welcome-close-heading"
              className="max-w-[16ch] scroll-mt-20 text-3xl font-semibold tracking-tight text-pretty md:text-4xl lg:text-5xl"
            >
              {signedIn ? "The docket is ready" : "Open a docket of your own"}
            </h2>
            <p className="mt-4 max-w-[52ch] text-base leading-relaxed text-white/75">
              {signedIn
                ? "Paste a question and a generated answer, then inspect the claims yourself."
                : "Create an account to paste a question and a generated answer, then inspect the claims yourself."}
            </p>
            <WelcomeActions className="mt-8" />
          </div>
        </section>
      </main>
      <WelcomeFooter />
    </div>
  );
}

const primaryClass =
  "inline-flex min-h-11 whitespace-nowrap items-center justify-center gap-2 rounded-full bg-accent px-5 text-sm font-semibold text-accent-fg no-underline transition-[opacity,transform] duration-150 hover:opacity-90 active:scale-[0.98]";

function WelcomeActions({ className }: { className?: string }) {
  const { isLoaded, isSignedIn } = useAuthStatus();

  return (
    <div className={["flex flex-wrap gap-3", className].filter(Boolean).join(" ")}>
      {!isLoaded ? (
        <p className="m-0 flex items-center">
          <span className="sr-only">Checking your session…</span>
          <span className="h-11 w-36 rounded-full bg-white/10" aria-hidden="true" />
        </p>
      ) : isSignedIn ? (
        <Link to="/evaluate" className={primaryClass}>
          Open the docket
          <ArrowRight size={16} weight="regular" aria-hidden="true" />
        </Link>
      ) : (
        <Link to="/sign-up" className={primaryClass}>
          Create account
          <ArrowRight size={16} weight="regular" aria-hidden="true" />
        </Link>
      )}
    </div>
  );
}
