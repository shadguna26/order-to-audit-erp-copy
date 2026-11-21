/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        page: 'var(--bg-page)',
        card: {
          DEFAULT: 'var(--bg-card)',
          subtle: 'var(--bg-card-subtle)'
        },
        soil: {
          DEFAULT: 'var(--text-main)',
          muted: 'var(--text-muted)'
        },
        terracotta: {
          DEFAULT: 'var(--accent-terracotta)',
          hover: 'var(--accent-terracotta-hover)'
        },
        leaf: {
          DEFAULT: 'var(--success-leaf)',
          hover: 'var(--success-leaf-hover)'
        },
        turmeric: {
          DEFAULT: 'var(--warning-turmeric)',
          hover: 'var(--warning-turmeric-hover)'
        },
        chilli: {
          DEFAULT: 'var(--danger-chilli)',
          hover: 'var(--danger-chilli-hover)'
        },
        'card-border': 'var(--border-card)'
      },
      fontFamily: {
        heading: ['Fraunces', 'Noto Serif Tamil', 'serif'],
        body: ['Inter', 'Mukta', 'Noto Sans Tamil', 'sans-serif'],
        tamil: ['Noto Sans Tamil', 'sans-serif'],
        'tamil-heading': ['Noto Serif Tamil', 'serif']
      }
    },
  },
  plugins: [],
}
