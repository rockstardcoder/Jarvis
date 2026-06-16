/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        background: "#070B12",
        surface: "#0B111B",
        "surface-soft": "#0E1624",
        "surface-card": "#101A2A",
        "surface-raised": "#132033",

        primary: "#F4F8FF",
        secondary: "#AAB7C8",
        muted: "#6F7F95",

        "primary-container": "#22D3EE",
        "primary-blue": "#3B82F6",
        "primary-green": "#10B981",

        success: "#22C55E",
        warning: "#FACC15",
        danger: "#FF4D5E",
      },
      spacing: {
        "container-padding": "24px",
      },
      borderRadius: {
        xl: "24px",
        "2xl": "32px",
      },
      boxShadow: {
        glow: "0 0 26px rgba(34,211,238,0.34)",
        "glow-blue": "0 0 34px rgba(59,130,246,0.34)",
        "glow-soft": "0 0 18px rgba(34,211,238,0.18)",
        "card-depth": "0 20px 60px rgba(0,0,0,0.35)",
      },
      fontFamily: {
        sans: ["Inter", "Segoe UI", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "Consolas", "monospace"],
      },
    },
  },
  plugins: [],
};