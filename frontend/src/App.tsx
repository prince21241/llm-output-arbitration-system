import { AuthenticateWithRedirectCallback, useAuth } from "@clerk/react";
import { Navigate, Route, Routes } from "react-router-dom";
import { EvaluatePage } from "./components/EvaluatePage";
import { ProtectedRoute } from "./components/ProtectedRoute";
import { SignInPage } from "./components/SignInPage";
import { SignUpPage } from "./components/SignUpPage";
import { WelcomePage } from "./components/WelcomePage";

function HomeRedirect() {
  const { isLoaded, isSignedIn } = useAuth();
  if (!isLoaded) {
    return (
      <div className="flex min-h-[100dvh] items-center justify-center bg-canvas text-sm text-muted">
        Checking your session…
      </div>
    );
  }
  return <Navigate to={isSignedIn ? "/welcome" : "/sign-in"} replace />;
}

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<HomeRedirect />} />
      <Route path="/sign-in/*" element={<SignInPage />} />
      <Route path="/sign-up/*" element={<SignUpPage />} />
      <Route
        path="/sso-callback"
        element={<AuthenticateWithRedirectCallback />}
      />
      <Route element={<ProtectedRoute />}>
        <Route path="/welcome" element={<WelcomePage />} />
        <Route path="/evaluate" element={<EvaluatePage />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
