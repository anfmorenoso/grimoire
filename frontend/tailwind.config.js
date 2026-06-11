/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        surface: "#0e0e0e",
        card: "#1a1a1a",
        border: "#2a2a2a",
        accent: "#a78bfa",
        muted: "#6b7280",
      },
    },
  },
  plugins: [],
};
