/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'tg-bg': 'var(--tg-bg)',
        'tg-text': 'var(--tg-text)',
        'tg-button': 'var(--tg-button)',
      },
      animation: {
        'fade-in': 'fadeIn 0.3s ease forwards',
        'pulse-glow': 'pulseGlow 2s infinite',
      }
    },
  },
  plugins: [],
}
