import { AuthenticateWithRedirectCallback } from "@clerk/react";
import { Navigate, Route, Routes } from "react-router-dom";
import { EvaluatePage } from "./components/EvaluatePage";
import { MissingClerkKeys } from "./components/MissingClerkKeys";
import { ProtectedRoute } from "./components/ProtectedRoute";
import { SignInPage } from "./components/SignInPage";
import { SignUpPage } from "./components/SignUpPage";
import { WelcomePage } from "./components/WelcomePage";

export default function App({
  clerkEnabled = true,
}: {
  clerkEnabled?: boolean;
}) {
  if (!clerkEnabled) {
    return (
      <Routes>
        <Route path="/" element={<WelcomePage />} />
        <Route path="/welcome" element={<Navigate to="/" replace />} />
        <Route path="*" element={<MissingClerkKeys />} />
      </Routes>
    );
  }

  return (
    <Routes>
      <Route path="/" element={<WelcomePage />} />
      <Route path="/welcome" element={<Navigate to="/" replace />} />
      <Route path="/sign-in/*" element={<SignInPage />} />
      <Route path="/sign-up/*" element={<SignUpPage />} />
      <Route
        path="/sso-callback"
        element={<AuthenticateWithRedirectCallback />}
      />
      <Route element={<ProtectedRoute />}>
        <Route path="/evaluate" element={<EvaluatePage />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
