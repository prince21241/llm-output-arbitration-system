import { Navigate } from "react-router-dom";
import { SignIn, useAuth } from "@clerk/react";
import { Header } from "./Header";

export function SignInPage() {
  const { isLoaded, isSignedIn } = useAuth();

  if (isLoaded && isSignedIn) {
    return <Navigate to="/evaluate" replace />;
  }

  return (
    <div className="min-h-[100dvh] bg-canvas text-ink">
      <Header />
      <main className="mx-auto flex max-w-[1400px] justify-center px-4 py-10">
        <div className="w-full max-w-md">
          <h1 className="text-2xl font-semibold tracking-tight">Sign in</h1>
          <p className="mt-2 max-w-[65ch] text-sm leading-relaxed text-muted">
            Use your account to reach the evaluate docket.
          </p>
          <div className="mt-6">
            <SignIn
              routing="path"
              path="/sign-in"
              signUpUrl="/sign-up"
              fallbackRedirectUrl="/evaluate"
              forceRedirectUrl="/evaluate"
            />
          </div>
        </div>
      </main>
    </div>
  );
}
