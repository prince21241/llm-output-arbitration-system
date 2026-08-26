import { Navigate } from "react-router-dom";
import { SignUp, useAuth } from "@clerk/react";
import { Header } from "./Header";

export function SignUpPage() {
  const { isLoaded, isSignedIn } = useAuth();

  if (isLoaded && isSignedIn) {
    return <Navigate to="/welcome" replace />;
  }

  return (
    <div className="min-h-[100dvh] bg-canvas text-ink">
      <Header />
      <main className="mx-auto flex max-w-[1400px] justify-center px-4 py-10">
        <div className="w-full max-w-md">
          <h1 className="text-2xl font-semibold tracking-tight">Create an account</h1>
          <p className="mt-2 max-w-[65ch] text-sm leading-relaxed text-muted">
            After you sign up, you land on a short welcome page, then the docket.
          </p>
          <div className="mt-6">
            <SignUp
              routing="path"
              path="/sign-up"
              signInUrl="/sign-in"
              fallbackRedirectUrl="/welcome"
              forceRedirectUrl="/welcome"
            />
          </div>
        </div>
      </main>
    </div>
  );
}
