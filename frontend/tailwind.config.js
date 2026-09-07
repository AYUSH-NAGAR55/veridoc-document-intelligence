/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#1B1F23",
        inkmuted: "#5B6470",
        canvas: "#FAF9F6",
        surface: "#FFFFFF",
        line: "#E7E4DD",
        blue: { pastel: "#DCE9FB", deep: "#3D63DD" },
        lavender: { pastel: "#EAE4FB", deep: "#7C6FE0" },
        mint: { pastel: "#DFF3EA", deep: "#1F9C77" },
        peach: { pastel: "#FCE8DD", deep: "#E0794A" },
        danger: { pastel: "#FBE1E1", deep: "#D64545" },
      },
      fontFamily: {
        sans: ["Inter", "ui-sans-serif", "system-ui", "sans-serif"],
        mono: ["'IBM Plex Mono'", "ui-monospace", "SFMono-Regular", "monospace"],
      },
      borderRadius: {
        xl2: "1.25rem",
      },
      boxShadow: {
        soft: "0 1px 2px rgba(27,31,35,0.04), 0 8px 24px -12px rgba(27,31,35,0.10)",
        card: "0 1px 3px rgba(27,31,35,0.06), 0 1px 2px rgba(27,31,35,0.04)",
      },
      keyframes: {
        float: {
          "0%, 100%": { transform: "translateY(0px) rotate(var(--r, 0deg))" },
          "50%": { transform: "translateY(-10px) rotate(var(--r, 0deg))" },
        },
        drift: {
          "0%": { transform: "translateY(0)" },
          "100%": { transform: "translateY(-16px)" },
        },
        dash: {
          to: { strokeDashoffset: 0 },
        },
        pulseRing: {
          "0%": { transform: "scale(0.9)", opacity: "0.6" },
          "70%": { transform: "scale(1.4)", opacity: "0" },
          "100%": { opacity: "0" },
        },
      },
      animation: {
        float: "float 6s ease-in-out infinite",
        dash: "dash 1.4s ease-out forwards",
        pulseRing: "pulseRing 2.2s ease-out infinite",
      },
    },
  },
  plugins: [],
};
