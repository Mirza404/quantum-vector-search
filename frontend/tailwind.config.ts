import type { Config } from 'tailwindcss'

export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        brand: {
          DEFAULT: '#7c3aed',
          muted: '#ede9fe',
        },
      },
      fontFamily: {
        sans: ['"Inter var"', 'Inter', 'system-ui', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'ui-monospace', 'SFMono-Regular', 'monospace'],
      },
      boxShadow: {
        card: '0 10px 25px -12px rgba(15, 23, 42, 0.35)',
      },
    },
  },
  plugins: [],
} satisfies Config

