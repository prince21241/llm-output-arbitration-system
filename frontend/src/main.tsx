import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter, useNavigate } from "react-router-dom";
import { ClerkProvider } from "@clerk/react";
import App from "./App.tsx";
import { MissingClerkKeys } from "./components/MissingClerkKeys.tsx";
import { CLERK_PUBLISHABLE_KEY, clerkAppearance } from "./lib/clerk.ts";
import { ThemeProvider, useTheme } from "./lib/theme.tsx";
import "./index.css";

function ClerkRoot() {
  const navigate = useNavigate();
  const { theme } = useTheme();

  if (!CLERK_PUBLISHABLE_KEY) {
    return <MissingClerkKeys />;
  }

  return (
    <ClerkProvider
      publishableKey={CLERK_PUBLISHABLE_KEY}
      appearance={clerkAppearance(theme)}
      signInUrl="/sign-in"
      signUpUrl="/sign-up"
      signInFallbackRedirectUrl="/welcome"
      signUpFallbackRedirectUrl="/welcome"
      afterSignOutUrl="/sign-in"
      routerPush={(to) => navigate(to)}
      routerReplace={(to) => navigate(to, { replace: true })}
    >
      <App />
    </ClerkProvider>
  );
}

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <ThemeProvider>
      <BrowserRouter>
        <ClerkRoot />
      </BrowserRouter>
    </ThemeProvider>
  </StrictMode>,
);
