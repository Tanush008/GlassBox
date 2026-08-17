import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        deep: "#0B0E14",
        panel: "#12161F",
        line: "rgba(255,255,255,0.08)",
        ink: "#E6E9EF",
        muted: "#8B93A7",
        faint: "#525A6E",
        planner: "#E8A33D",
        coder: "#5EEAD4",
        reviewer: "#A78BFA",
        approve: "#34D399",
        changes: "#FB7185",
      },
      fontFamily: {
        display: ["var(--font-display)", "sans-serif"],
        body: ["var(--font-body)", "sans-serif"],
        mono: ["var(--font-mono)", "monospace"],
      },
      keyframes: {
        rise: {
          "0%": { opacity: "0", transform: "translateY(6px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        fillbar: {
          "0%": { width: "0%" },
        },
      },
      animation: {
        rise: "rise 0.35s ease-out both",
      },
    },
  },
  plugins: [],
};
export default config;
