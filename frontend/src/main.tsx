import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter, useNavigate } from "react-router-dom";
import { ClerkProvider } from "@clerk/react";
import App from "./App.tsx";
import { AnonAuthStatus, ClerkAuthStatus } from "./lib/authStatus.tsx";
import { CLERK_PUBLISHABLE_KEY, clerkAppearance } from "./lib/clerk.ts";
import "./index.css";

function ClerkRoot() {
  const navigate = useNavigate();

  if (!CLERK_PUBLISHABLE_KEY) {
    return (
      <AnonAuthStatus>
        <App clerkEnabled={false} />
      </AnonAuthStatus>
    );
  }

  return (
    <ClerkProvider
      publishableKey={CLERK_PUBLISHABLE_KEY}
      appearance={clerkAppearance()}
      signInUrl="/sign-in"
      signUpUrl="/sign-up"
      signInFallbackRedirectUrl="/evaluate"
      signUpFallbackRedirectUrl="/evaluate"
      afterSignOutUrl="/"
      routerPush={(to) => navigate(to)}
      routerReplace={(to) => navigate(to, { replace: true })}
    >
      <ClerkAuthStatus>
        <App />
      </ClerkAuthStatus>
    </ClerkProvider>
  );
}

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <BrowserRouter>
      <ClerkRoot />
    </BrowserRouter>
  </StrictMode>,
);
