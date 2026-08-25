import { Moon, Sun } from "@phosphor-icons/react";
import { useTheme } from "../lib/theme";

export function ThemeToggle() {
  const { theme, toggleTheme } = useTheme();
  const next = theme === "dark" ? "light" : "dark";

  return (
    <button
      type="button"
      onClick={toggleTheme}
      aria-label={`Switch to ${next} mode`}
      className="inline-flex h-11 w-11 items-center justify-center rounded-md text-ink transition-transform duration-150 hover:bg-inset active:scale-[0.98] md:h-9 md:w-9"
    >
      {theme === "dark" ? (
        <Sun size={18} weight="regular" aria-hidden="true" />
      ) : (
        <Moon size={18} weight="regular" aria-hidden="true" />
      )}
    </button>
  );
}
