/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        ledger: {
          950: "#0A1B2E", // deep navy — primary surface
          900: "#0F2438",
          800: "#173352",
          700: "#20456B",
          600: "#33608C",
        },
        parchment: {
          50: "#FBF9F4",
          100: "#F5F1E7",
          200: "#EAE3D2",
        },
        amber: {
          500: "#C8863A", // citation / highlight accent
          600: "#B0752F",
        },
        flag: {
          low: "#8AA24C",
          medium: "#D9A441",
          high: "#C1523B",
        },
      },
      fontFamily: {
        serif: ["\"Source Serif 4\"", "Georgia", "serif"],
        sans: ["\"Inter\"", "system-ui", "sans-serif"],
        mono: ["\"JetBrains Mono\"", "monospace"],
      },
    },
  },
  plugins: [],
};
