import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        // ClassQuest palette — "Find your classroom."
        sky: {
          DEFAULT: "#3b82f6", // warm sky blue (primary)
          50: "#eff6ff",
          100: "#dbeafe",
          500: "#3b82f6",
          600: "#2563eb",
          700: "#1d4ed8",
        },
        sunshine: {
          DEFAULT: "#fbbf24", // soft yellow accent
          100: "#fef3c7",
          400: "#fbbf24",
          500: "#f59e0b",
        },
        grow: {
          DEFAULT: "#22c55e", // green for high relevance scores
          100: "#dcfce7",
          500: "#22c55e",
          600: "#16a34a",
        },
      },
      fontFamily: {
        sans: ["var(--font-inter)", "system-ui", "sans-serif"],
      },
    },
  },
  plugins: [],
};

export default config;
