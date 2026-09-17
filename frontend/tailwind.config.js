/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        paper: "#FAF8F4",
        surface: "#FFFFFF",
        ink: "#3A3A42",
        "ink-soft": "#6B6B76",
        border: "#E7E2D8",
        primary: {
          DEFAULT: "#8FA6C9",
          soft: "#C9D6E8",
          deep: "#5E7BA3",
        },
        rose: {
          DEFAULT: "#D9A79C",
          soft: "#E8D5D0",
        },
        sage: {
          DEFAULT: "#7FA894",
          soft: "#CFE3D8",
        },
        amber: {
          DEFAULT: "#C98F5E",
          soft: "#E8D3B8",
        },
      },
      fontFamily: {
        display: ["Fraunces", "serif"],
        body: ["Inter", "sans-serif"],
        mono: ["JetBrains Mono", "monospace"],
      },
      borderRadius: {
        xl2: "1.25rem",
      },
      boxShadow: {
        soft: "0 1px 2px rgba(58, 58, 66, 0.04), 0 4px 16px rgba(58, 58, 66, 0.05)",
        lift: "0 2px 4px rgba(58, 58, 66, 0.06), 0 12px 28px rgba(58, 58, 66, 0.08)",
      },
      keyframes: {
        fadeIn: { "0%": { opacity: 0, transform: "translateY(6px)" }, "100%": { opacity: 1, transform: "translateY(0)" } },
      },
      animation: {
        fadeIn: "fadeIn 0.4s ease-out both",
      },
    },
  },
  plugins: [],
}
