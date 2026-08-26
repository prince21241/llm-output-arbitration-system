import { Scales } from "@phosphor-icons/react";
import { ThemeToggle } from "./ThemeToggle";

export function MissingClerkKeys() {
  return (
    <div className="min-h-[100dvh] bg-canvas text-ink">
      <header className="border-b border-line bg-canvas">
        <div className="mx-auto flex h-16 max-w-[1400px] items-center gap-3 px-4">
          <p className="inline-flex items-center gap-2 text-ink">
            <Scales size={22} weight="regular" aria-hidden="true" />
            <span className="text-[17px] font-semibold tracking-tight">
              Arbitrator
            </span>
          </p>
          <div className="ml-auto">
            <ThemeToggle />
          </div>
        </div>
      </header>
      <main className="mx-auto max-w-[65ch] px-4 py-12">
        <h1 className="text-3xl font-semibold tracking-tight">
          Add Clerk keys to enable sign-in
        </h1>
        <p className="mt-3 text-base leading-relaxed text-muted">
          Create an application at{" "}
          <a
            href="https://dashboard.clerk.com"
            className="font-medium text-accent underline-offset-2 hover:underline"
          >
            dashboard.clerk.com
          </a>
          , then put the publishable key in frontend/.env and the secret key in
          backend/.env. Restart Vite and the API after saving.
        </p>
        <ol className="mt-6 list-decimal space-y-2 pl-5 text-sm leading-relaxed text-ink">
          <li>
            Frontend: <code className="font-mono text-[13px]">VITE_CLERK_PUBLISHABLE_KEY</code>
          </li>
          <li>
            Backend: <code className="font-mono text-[13px]">CLERK_SECRET_KEY</code>
          </li>
        </ol>
      </main>
    </div>
  );
}
