/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        gov: {
          saffron: "#FF9933",
          navy: "#000080",
          green: "#138808",
          dark: "#0F172A",
          card: "#1E293B",
          accent: "#2563EB",
        }
      }
    },
  },
  plugins: [],
}
