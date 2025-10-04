/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        primary: "#2563eb", // 파란색 계열
        accent: "#10b981",  // 초록색 계열
      },
      borderRadius: {
        '2xl': '1rem',
      },
    },
  },
  plugins: [],
};
