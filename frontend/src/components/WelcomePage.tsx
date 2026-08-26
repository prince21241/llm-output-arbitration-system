import { ArrowRight, Scales } from "@phosphor-icons/react";
import { Link } from "react-router-dom";
import { useUser } from "@clerk/react";
import { motion, useReducedMotion } from "motion/react";
import { Header } from "./Header";

export function WelcomePage() {
  const { user, isLoaded } = useUser();
  const reduceMotion = useReducedMotion();
  const name = user?.firstName?.trim() || user?.username || "there";

  return (
    <div className="min-h-[100dvh] bg-canvas text-ink">
      <Header />
      <main className="mx-auto max-w-[1400px] px-4 py-10 lg:py-16">
        <motion.section
          initial={reduceMotion ? false : { opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={
            reduceMotion
              ? { duration: 0 }
              : { type: "spring", stiffness: 280, damping: 28 }
          }
          className="max-w-2xl rounded-lg border border-line bg-raised p-6 shadow-[0_1px_0_var(--shadow)] md:p-8"
        >
          <p className="inline-flex items-center gap-2 text-sm font-medium text-muted">
            <Scales size={16} weight="regular" aria-hidden="true" />
            Signed in
          </p>
          <h1 className="mt-3 max-w-[22ch] text-3xl font-semibold tracking-tight md:text-4xl">
            {isLoaded ? `Welcome, ${name}.` : "Welcome."}
          </h1>
          <p className="mt-3 max-w-[65ch] text-base leading-relaxed text-muted">
            This workspace extracts claims from a model answer, collects
            independent judge votes, and scores agreement with the calibrated
            confidence model.
          </p>
          <div className="mt-8 flex flex-wrap gap-3">
            <Link
              to="/evaluate"
              className="inline-flex min-h-11 items-center justify-center gap-2 rounded-md bg-accent px-4 text-sm font-semibold text-accent-fg no-underline hover:opacity-90 active:scale-[0.98]"
            >
              Open the docket
              <ArrowRight size={16} weight="regular" aria-hidden="true" />
            </Link>
            <p className="self-center text-sm text-muted">
              Paste a question and the generated answer to begin.
            </p>
          </div>
        </motion.section>
      </main>
    </div>
  );
}
