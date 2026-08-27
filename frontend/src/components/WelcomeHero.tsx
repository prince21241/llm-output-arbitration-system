import { ArrowUpRight, Pause, Play } from "@phosphor-icons/react";
import { Link } from "react-router-dom";
import { motion, useReducedMotion } from "motion/react";
import { useEffect, useRef, useState } from "react";
import { useAuthStatus } from "../lib/authStatus";
import { WelcomeParticles } from "./WelcomeParticles";

const HERO_VIDEO =
  "https://strvid.nyc3.cdn.digitaloceanspaces.com/motionsite/bg-red-ball.mp4";

const FEATURES = [
  {
    id: "01",
    title: "Extract claims",
    body: "The answer is split into checkable statements. Dates, numbers, and facts are tagged.",
  },
  {
    id: "02",
    title: "Collect votes",
    body: "Independent judges rule on each claim with a verdict, a confidence, and a short reason.",
  },
  {
    id: "03",
    title: "Score agreement",
    body: "Votes and evidence overlap become a preliminary confidence score. It is not a guarantee.",
  },
] as const;

export function WelcomeHero() {
  const reduceMotion = useReducedMotion();
  const videoRef = useRef<HTMLVideoElement>(null);
  const [videoReady, setVideoReady] = useState(false);
  const [paused, setPaused] = useState(Boolean(reduceMotion));

  useEffect(() => {
    setPaused(Boolean(reduceMotion));
  }, [reduceMotion]);

  useEffect(() => {
    const video = videoRef.current;
    if (!video) return;
    if (paused) {
      video.pause();
      return;
    }
    void video.play().catch(() => {
      setPaused(true);
    });
  }, [paused]);

  const showAtmosphere = !reduceMotion && !paused;

  return (
    <section
      id="how-it-works"
      className="relative isolate min-h-[100dvh] scroll-mt-20 overflow-hidden"
    >
      <video
        ref={videoRef}
        className="absolute inset-0 z-0 h-full w-full object-cover object-center"
        autoPlay={!reduceMotion}
        loop
        muted
        playsInline
        preload="metadata"
        aria-hidden="true"
        onCanPlay={() => setVideoReady(true)}
        onError={() => setVideoReady(false)}
      >
        <source src={HERO_VIDEO} type="video/mp4" />
      </video>
      <div
        className="welcome-vignette pointer-events-none absolute inset-0 z-[1]"
        aria-hidden="true"
      />
      {showAtmosphere ? <WelcomeParticles paused={false} /> : null}
      {!videoReady ? (
        <div className="absolute inset-0 z-0 bg-[#080104]" aria-hidden="true" />
      ) : null}

      <div className="relative z-[3] mx-auto grid min-h-[100dvh] max-w-[1400px] grid-cols-1 content-center gap-10 px-4 pb-16 pt-24 lg:grid-cols-12 lg:items-center lg:gap-8">
        <motion.div
          className="lg:col-span-5"
          initial={reduceMotion ? false : { opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={
            reduceMotion
              ? { duration: 0 }
              : { duration: 0.55, ease: [0.16, 1, 0.3, 1] }
          }
        >
          <p className="text-xs font-bold uppercase tracking-[0.3em] text-[#e6004c] sm:text-sm">
            Forensic workspace
          </p>
          <h1 className="mt-4 max-w-[11ch] text-5xl font-black uppercase leading-[0.96] tracking-tight text-[#f2f3f4] sm:text-7xl lg:text-[80px]">
            Inspect every claim
          </h1>
          <p className="mt-5 max-w-[36ch] text-base leading-relaxed text-white/75 md:text-lg">
            Paste a question and a model answer. Independent judges vote, then
            you get a preliminary score.
          </p>
          <HeroActions />
        </motion.div>

        <div
          className="hidden min-h-[12rem] lg:col-span-3 lg:block"
          aria-hidden="true"
        />

        <motion.ol
          className="grid gap-0 lg:col-span-4"
          initial={reduceMotion ? false : { opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={
            reduceMotion
              ? { duration: 0 }
              : { duration: 0.55, delay: 0.08, ease: [0.16, 1, 0.3, 1] }
          }
        >
          {FEATURES.map((feature, index) => (
            <li
              key={feature.id}
              className={
                index < FEATURES.length - 1
                  ? "border-b border-white/15 py-5 first:pt-0"
                  : "py-5 first:pt-0"
              }
            >
              <p className="font-mono text-xs tabular-nums text-[#ff1053]">
                {feature.id}
              </p>
              <h2 className="mt-2 text-lg font-semibold tracking-tight text-[#f2f3f4]">
                {feature.title}
              </h2>
              <p className="mt-2 max-w-[36ch] text-sm leading-relaxed text-white/75">
                {feature.body}
              </p>
            </li>
          ))}
        </motion.ol>
      </div>

      {!reduceMotion ? (
        <button
          type="button"
          className="welcome-glass absolute bottom-5 left-4 z-[3] inline-flex min-h-11 items-center gap-2 rounded-full px-4 text-sm font-medium text-[#f2f3f4]"
          aria-pressed={paused}
          onClick={() => setPaused((current) => !current)}
        >
          {paused ? (
            <Play size={16} weight="regular" aria-hidden="true" />
          ) : (
            <Pause size={16} weight="regular" aria-hidden="true" />
          )}
          {paused ? "Play background" : "Pause background"}
        </button>
      ) : null}
    </section>
  );
}

const primaryClass =
  "inline-flex min-h-11 whitespace-nowrap items-center justify-center gap-2 rounded-full bg-accent px-5 text-sm font-semibold text-accent-fg no-underline transition-[opacity,transform] duration-150 hover:opacity-90 active:scale-[0.98]";

const secondaryClass =
  "welcome-glass inline-flex min-h-11 whitespace-nowrap items-center justify-center rounded-full px-5 text-sm font-medium text-[#f2f3f4] no-underline transition-[border-color,transform] duration-150 hover:border-white/80 active:scale-[0.98]";

function HeroActions() {
  const { isLoaded, isSignedIn } = useAuthStatus();

  return (
    <div className="mt-8 flex flex-wrap gap-3">
      {!isLoaded ? (
        <p className="m-0 flex items-center">
          <span className="sr-only">Checking your session…</span>
          <span className="h-11 w-36 rounded-full bg-white/10" aria-hidden="true" />
        </p>
      ) : isSignedIn ? (
        <Link to="/evaluate" className={primaryClass}>
          Open the docket
          <ArrowUpRight size={16} weight="regular" aria-hidden="true" />
        </Link>
      ) : (
        <>
          <Link to="/sign-up" className={primaryClass}>
            Create account
            <ArrowUpRight size={16} weight="regular" aria-hidden="true" />
          </Link>
          <Link to="/sign-in" className={secondaryClass}>
            Sign in
          </Link>
        </>
      )}
    </div>
  );
}
