import type { Theme } from "./theme";

export const CLERK_PUBLISHABLE_KEY = import.meta.env.VITE_CLERK_PUBLISHABLE_KEY ?? "";

export function clerkAppearance(theme: Theme) {
  const dark = theme === "dark";
  return {
    variables: {
      colorPrimary: dark ? "#2dd4bf" : "#0f766e",
      colorBackground: dark ? "#1b1c20" : "#f7f8f9",
      colorForeground: dark ? "#f2f3f4" : "#1a1c1f",
      colorMutedForeground: dark ? "#a7adb6" : "#5c6168",
      colorInput: dark ? "#0e0f12" : "#e4e6ea",
      colorNeutral: dark ? "#a7adb6" : "#5c6168",
      borderRadius: "0.5rem",
      fontFamily: '"Outfit Variable", ui-sans-serif, system-ui, sans-serif',
    },
    layout: {
      socialButtonsVariant: "blockButton" as const,
      socialButtonsPlacement: "bottom" as const,
    },
  };
}
