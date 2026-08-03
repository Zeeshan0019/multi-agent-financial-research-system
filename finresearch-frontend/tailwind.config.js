/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        // "ledger" = ink scale: deep violet-black, used for the sidebar
        // surface and as primary text color throughout.
        ledger: {
          950: "#1E1B3C",
          900: "#2A2456",
          800: "#372E72",
          700: "#473C93",
          600: "#5A4BB0",
        },
        // "parchment" = page background scale: soft lavender-white instead
        // of stark white, so panels have somewhere to pop against.
        parchment: {
          50: "#FDFCFF",
          100: "#F4F1FF",
          200: "#E8E2FB",
        },
        // Citation / highlight accent — warm amber, unmistakably distinct
        // from the cool brand palette so a source tab always reads as one.
        amber: {
          100: "#FEF0D8",
          500: "#F5A524",
          600: "#DB8B0B",
        },
        // Secondary brand accents — used for interactive states and to
        // give each company in a comparison its own identity color.
        teal: {
          100: "#CCFBF1",
          500: "#14B8A6",
          600: "#0D9488",
        },
        violet: {
          100: "#EDE7FE",
          500: "#8B5CF6",
          600: "#7C3AED",
        },
        coral: {
          100: "#FFE4E8",
          500: "#FB7185",
          600: "#F43F5E",
        },
        // Semantic risk colors, kept vivid rather than muted.
        flag: {
          low: "#16A34A",
          medium: "#F97316",
          high: "#E11D48",
        },
      },
      fontFamily: {
        display: ["\"Space Grotesk\"", "system-ui", "sans-serif"],
        sans: ["\"Inter\"", "system-ui", "sans-serif"],
        mono: ["\"JetBrains Mono\"", "monospace"],
      },
      backgroundImage: {
        "brand-mesh":
          "radial-gradient(at 15% 0%, rgba(139,92,246,0.16) 0px, transparent 55%), radial-gradient(at 85% 10%, rgba(20,184,166,0.14) 0px, transparent 50%), radial-gradient(at 50% 100%, rgba(251,113,133,0.10) 0px, transparent 55%)",
        "brand-gradient": "linear-gradient(135deg, #7C3AED 0%, #5A4BB0 50%, #0D9488 100%)",
      },
    },
  },
  plugins: [],
};
