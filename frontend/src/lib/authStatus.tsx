import {
  createContext,
  useContext,
  type ReactNode,
} from "react";
import { useAuth } from "@clerk/react";

type AuthStatus = {
  clerkEnabled: boolean;
  isLoaded: boolean;
  isSignedIn: boolean;
};

const AuthStatusContext = createContext<AuthStatus>({
  clerkEnabled: false,
  isLoaded: true,
  isSignedIn: false,
});

export function AnonAuthStatus({ children }: { children: ReactNode }) {
  return (
    <AuthStatusContext.Provider
      value={{ clerkEnabled: false, isLoaded: true, isSignedIn: false }}
    >
      {children}
    </AuthStatusContext.Provider>
  );
}

export function ClerkAuthStatus({ children }: { children: ReactNode }) {
  const { isLoaded, isSignedIn } = useAuth();
  return (
    <AuthStatusContext.Provider
      value={{
        clerkEnabled: true,
        isLoaded,
        isSignedIn: Boolean(isSignedIn),
      }}
    >
      {children}
    </AuthStatusContext.Provider>
  );
}

export function useAuthStatus() {
  return useContext(AuthStatusContext);
}
