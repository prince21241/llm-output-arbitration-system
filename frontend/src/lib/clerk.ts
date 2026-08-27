export const CLERK_PUBLISHABLE_KEY = import.meta.env.VITE_CLERK_PUBLISHABLE_KEY ?? "";

export function clerkAppearance() {
  return {
    variables: {
      colorPrimary: "#2dd4bf",
      colorBackground: "#1b1c20",
      colorForeground: "#f2f3f4",
      colorMutedForeground: "#a7adb6",
      colorInput: "#0e0f12",
      colorNeutral: "#a7adb6",
      borderRadius: "0.5rem",
      fontFamily: '"Outfit Variable", ui-sans-serif, system-ui, sans-serif',
    },
    layout: {
      socialButtonsVariant: "blockButton" as const,
      socialButtonsPlacement: "bottom" as const,
    },
  };
}
